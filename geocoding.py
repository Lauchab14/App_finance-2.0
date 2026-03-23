"""
geocoding.py — Module de géocodage et d'analyse de localisation via OpenStreetMap
"""
import requests
import time
from typing import List, Dict, Optional, Tuple
import math
import os
import re
from urllib.parse import quote
import openrouteservice
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Agent utilisateur obligatoire pour Nominatim (OpenStreetMap)
# Nominatim exige un User-Agent unique et descriptif, sinon il bloque les requêtes (403)
USER_AGENT = "AnalyseurRentabiliteQC/2.1 (university-project; streamlit-app)"
TOMTOM_BASE_URL = "https://api.tomtom.com"
TOMTOM_LANGUAGE = "fr-CA"
TOMTOM_COUNTRYSET = "CA"
TOMTOM_MAX_RESULTS_PER_CATEGORY = 12
TOMTOM_ROUTE_CANDIDATES = 8

def _get_tomtom_api_key() -> str:
    """Retourne la cle TomTom nettoyee, sans guillemets parasites."""
    return os.getenv("TOMTOM_API_KEY", "").strip().strip('"').strip("'")


def _tomtom_enabled() -> bool:
    return bool(_get_tomtom_api_key())


def _tomtom_get(path: str, params: Optional[dict] = None, timeout: int = 8) -> dict:
    """Appel GET centralise vers TomTom."""
    api_key = _get_tomtom_api_key()
    if not api_key:
        raise RuntimeError("TOMTOM_API_KEY est absente.")

    request_params = {"key": api_key}
    if params:
        request_params.update({k: v for k, v in params.items() if v not in (None, "")})

    response = requests.get(f"{TOMTOM_BASE_URL}{path}", params=request_params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _tomtom_extract_city(address: dict) -> str:
    return (
        address.get("municipality")
        or address.get("municipalitySubdivision")
        or address.get("localName")
        or address.get("countrySecondarySubdivision")
        or ""
    )


def _tomtom_extract_state(address: dict) -> str:
    return (
        address.get("countrySubdivision")
        or address.get("countrySubdivisionName")
        or address.get("countrySecondarySubdivision")
        or ""
    )


def _tomtom_is_quebec(address: dict) -> bool:
    subdivision = _normalize_service_name(_tomtom_extract_state(address))
    subdivision_code = (address.get("countrySubdivisionCode") or "").upper()
    freeform = _normalize_service_name(address.get("freeformAddress", ""))

    return (
        subdivision in {"quebec", "québec", "qc"}
        or subdivision_code.endswith("-QC")
        or ", qc" in freeform
        or ", québec" in freeform
        or ", quebec" in freeform
    )


def _tomtom_address_label(address: dict) -> str:
    freeform = address.get("freeformAddress")
    if freeform:
        return freeform

    street_name = address.get("streetName", "")
    street_number = address.get("streetNumber", "")
    city = _tomtom_extract_city(address)
    state = _tomtom_extract_state(address)
    parts = [" ".join(part for part in [street_number, street_name] if part).strip(), city, state]
    return ", ".join(part for part in parts if part)


def _tomtom_result_to_suggestion(result: dict) -> Optional[Dict]:
    """Mappe un resultat TomTom vers la structure attendue par l'app."""
    address = result.get("address", {})
    position = result.get("position", {})
    lat = position.get("lat")
    lon = position.get("lon")
    if lat is None or lon is None or not _tomtom_is_quebec(address):
        return None

    ville = _tomtom_extract_city(address)
    raw_address = {
        "address": {
            "house_number": address.get("streetNumber", ""),
            "road": address.get("streetName", ""),
            "city": ville,
            "town": ville,
            "municipality": ville,
            "postcode": address.get("postalCode", ""),
            "state": _tomtom_extract_state(address),
        },
        "tomtom_result": result,
    }

    return {
        "display_name": _tomtom_address_label(address),
        "lat": float(lat),
        "lon": float(lon),
        "ville": ville,
        "raw": raw_address,
    }


def _tomtom_geocode(query: str, limit: int = 5, typeahead: bool = False) -> List[Dict]:
    data = _tomtom_get(
        f"/search/2/geocode/{quote(query, safe='')}.json",
        params={
            "limit": limit,
            "countrySet": TOMTOM_COUNTRYSET,
            "language": TOMTOM_LANGUAGE,
            "typeahead": str(typeahead).lower(),
        },
        timeout=8,
    )

    suggestions = []
    for result in data.get("results", []):
        mapped = _tomtom_result_to_suggestion(result)
        if mapped:
            suggestions.append(mapped)
    return suggestions


def _verifier_adresse_nominatim(adresse: str) -> Dict[str, str]:
    """
    Vérifie et géolocalise une adresse saisie via Nominatim.
    Retourne un dictionnaire avec le statut, latitude, longitude et l'adresse formatée.
    """
    if not adresse or len(adresse) < 5:
        return {"statut": "erreur", "message": "L'adresse saisie est trop courte."}

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": adresse,
        "format": "json",
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        time.sleep(0.5)

        data = response.json()
        if not data:
            return {
                "statut": "erreur",
                "message": "Adresse introuvable. Veuillez vérifier l'orthographe ou ajouter la ville et 'Québec'.",
            }

        # Prendre le premier résultat
        meilleur_resultat = data[0]
        adresse_formatee = meilleur_resultat.get("display_name", adresse)
        lat = float(meilleur_resultat.get("lat"))
        lon = float(meilleur_resultat.get("lon"))

        # Identifier la région grosso modo selon le nom pour appliquer les bonnes pondérations
        ville = "Inconnu"
        for part in adresse_formatee.split(","):
            if part.strip().lower() in ["montréal", "montreal", "laval", "longueuil"]:
                ville = part.strip()
                break
            elif part.strip().lower() in ["québec", "quebec", "lévis", "levis"]:
                ville = part.strip()
                break

        region = determiner_region_gps(lat, lon, ville)

        return {
            "statut": "succes",
            "lat": lat,
            "lon": lon,
            "adresse": adresse_formatee,
            "region": region,
        }

    except Exception as e:
        return {"statut": "erreur", "message": f"Erreur de connexion API : {str(e)}"}


def _rechercher_adresses_nominatim(requete: str) -> List[Dict]:
    """
    Recherche des adresses au Québec correspondant à la requête via Nominatim (OSM).
    Retourne une liste de dictionnaires avec 'display_name', 'lat' et 'lon'.
    """
    if not requete or len(requete) < 4:
        return []

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": requete,
        "format": "json",
        "addressdetails": 1,
        "countrycodes": "ca",
        "limit": 5,
        # Viewbox = west_lon, south_lat, east_lon, north_lat (priorité au Québec)
        "viewbox": "-80.0,44.0,-57.0,63.0",
        "bounded": 0,  # Ne pas exclure les résultats hors viewbox
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        time.sleep(0.5)  # Respecter la limite de Nominatim (1 req/sec max)

        resultats = response.json()
        suggestions = []

        for place in resultats:
            addr = place.get("address", {})
            state = addr.get("state", "")
            if state != "Quebec" and state != "Québec":
                continue  # S'assurer que c'est au Québec

            numero = addr.get("house_number", "")
            rue = addr.get("road", "")
            ville = addr.get("city", addr.get("town", addr.get("village", addr.get("municipality", ""))))

            # Formater une adresse propre
            if numero and rue and ville:
                nom_propre = f"{numero} {rue}, {ville}"
            else:
                nom_propre = place.get("display_name", "")

            suggestions.append(
                {
                    "display_name": nom_propre,
                    "lat": float(place["lat"]),
                    "lon": float(place["lon"]),
                    "ville": ville,
                    "raw": place,
                }
            )

        return suggestions
    except Exception as e:
        print(f"Erreur de géocodage: {e}")
        return []


def verifier_adresse(adresse: str) -> Dict[str, str]:
    """
    Vérifie et géolocalise une adresse, en privilégiant TomTom si la clé est disponible.
    Fallback automatique sur Nominatim pour préserver le fonctionnement actuel.
    """
    if not adresse or len(adresse) < 5:
        return {"statut": "erreur", "message": "L'adresse saisie est trop courte."}

    if _tomtom_enabled():
        try:
            suggestions = _tomtom_geocode(adresse, limit=3, typeahead=False)
            if suggestions:
                meilleur_resultat = suggestions[0]
                lat = float(meilleur_resultat["lat"])
                lon = float(meilleur_resultat["lon"])
                ville = meilleur_resultat.get("ville", "Inconnu")
                region = determiner_region_gps(lat, lon, ville)
                return {
                    "statut": "succes",
                    "lat": lat,
                    "lon": lon,
                    "adresse": meilleur_resultat["display_name"],
                    "region": region,
                }
        except Exception as e:
            print(f"TomTom verifier_adresse indisponible, fallback Nominatim: {e}")

    return _verifier_adresse_nominatim(adresse)


def rechercher_adresses(requete: str) -> List[Dict]:
    """
    Recherche des adresses au Québec, en privilégiant TomTom si disponible.
    La structure de sortie reste identique pour ne pas toucher au visuel.
    """
    if not requete or len(requete) < 4:
        return []

    if _tomtom_enabled():
        try:
            suggestions = _tomtom_geocode(requete, limit=5, typeahead=True)
            if suggestions:
                return suggestions
        except Exception as e:
            print(f"TomTom rechercher_adresses indisponible, fallback Nominatim: {e}")

    return _rechercher_adresses_nominatim(requete)


def determiner_region_gps(lat: float, lon: float, ville: str) -> str:
    """
    Détermine la région (Métropolitaine, Urbaine, Rurale) selon la ville ou les coordonnées GPS.
    """
    ville = ville.lower()

    # Dictionnaire simplifié pour mapper les villes aux régions
    villes_metro = ["montréal", "montreal", "laval", "longueuil", "brossard", "terrebonne", "repentigny",
                    "blainville", "mirabel", "saint-jérôme", "saint-jerome", "châteauguay", "chateauguay",
                    "saint-eustache", "vaudreuil", "mascouche", "boisbriand", "sainte-thérèse",
                    "boucherville", "saint-bruno", "varennes", "beloeil", "chambly", "carignan",
                    "deux-montagnes", "rosemère", "rosemere", "candiac", "la prairie", "saint-constant",
                    "saint-lambert", "saint-hubert", "saint-jean-sur-richelieu", "saint-jean"]
    villes_urbaines = ["québec", "quebec", "lévis", "levis", "gatineau", "sherbrooke",
                      "trois-rivières", "trois-rivieres", "saguenay", "chicoutimi", "jonquière",
                      "saint-nicolas", "charlesbourg", "beauport", "cap-rouge", "sainte-foy"]
    villes_semi = ["drummondville", "saint-hyacinthe", "granby", "victoriaville", "rimouski",
                  "shawinigan", "saint-georges", "thetford", "magog", "alma",
                  "rivière-du-loup", "riviere-du-loup", "val-d'or", "val-dor", "rouyn",
                  "joliette", "sorel", "sainte-marie", "ste-marie", "saint-raymond",
                  "montmagny", "la malbaie", "baie-comeau", "sept-îles", "sept-iles",
                  "matane", "amos", "cowansville", "saint-félicien", "roberval",
                  "saint-bernard", "beauceville", "saint-joseph", "lac-etchemin",
                  "saint-lazare", "sainte-julie", "terrebonne", "lachute", "hawkesbury"]

    for v in villes_metro:
        if v in ville:
            return "Métropolitaine (Montréal, Laval, Longueuil)"

    for v in villes_urbaines:
        if v in ville:
            return "Urbaine (Québec, Lévis, Gatineau, Sherbrooke)"

    for v in villes_semi:
        if v in ville:
            return "Semi-urbaine (Trois-Rivières, Drummondville, St-Hyacinthe)"

    # Par défaut ou si loin des grands centres
    return "Rurale (Beauce, Bas-St-Laurent, Abitibi, etc.)"


def _haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance en km entre deux points GPS (formule Haversine)."""
    R = 6371  # rayon de la Terre en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)


def _normalize_service_name(value: str) -> str:
    """Normalise legerement un nom pour la deduplication locale."""
    cleaned = (value or "").strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _service_text_blob(tags: dict, name: str) -> str:
    return " ".join(
        part for part in [
            _normalize_service_name(name),
            _normalize_service_name(str(tags.get("brand", ""))),
            _normalize_service_name(str(tags.get("brand:fr", ""))),
            _normalize_service_name(str(tags.get("operator", ""))),
        ] if part
    )


def _is_grocery_store(tags: dict, name: str) -> bool:
    shop = _normalize_service_name(tags.get("shop", ""))
    if shop in {"supermarket", "grocery", "greengrocer"} and not _is_specialty_food_place(name):
        return True

    blob = _service_text_blob(tags, name)
    grocery_markers = [
        " iga ",
        "metro",
        "super c",
        "maxi",
        "provigo",
        "adonis",
        "walmart",
        "costco",
        "marché tradition",
        "marche tradition",
        "bonichoix",
        "valumart",
        "marché ami",
        "marche ami",
        "intermarche",
    ]
    padded_blob = f" {blob} "
    return any(marker in padded_blob for marker in grocery_markers) and not _is_specialty_food_place(name)


def _is_pharmacy(tags: dict, name: str) -> bool:
    if (
        tags.get("amenity") == "pharmacy"
        or tags.get("shop") == "chemist"
        or tags.get("healthcare") == "pharmacy"
    ):
        return True

    blob = _service_text_blob(tags, name)
    pharmacy_markers = [
        "jean coutu",
        "uniprix",
        "pharmaprix",
        "brunet",
        "familiprix",
        "proxim",
    ]
    return any(marker in blob for marker in pharmacy_markers)


def _infer_school_bucket(tags: dict, name: str) -> Optional[str]:
    """
    Classe un etablissement scolaire dans une categorie utile a l'UI.
    Retourne None si l'entite ressemble plutot a une ecole specialisee
    (conduite, musique, adultes, etc.) qu'a une ecole primaire/secondaire.
    """
    amenity = (tags.get("amenity") or "").lower()
    if amenity == "kindergarten":
        return None
    if amenity == "college":
        return "cegep"
    if amenity == "university":
        return "universite"
    if amenity != "school":
        return None

    name_norm = _normalize_service_name(name)
    extra_fields = " ".join(
        _normalize_service_name(str(tags.get(key, "")))
        for key in ["school", "school:FR", "school:fr", "isced:level", "grades", "description"]
    )
    blob = f"{name_norm} {extra_fields}".strip()

    exclusion_markers = [
        "conduite",
        "driving",
        "musique",
        "music",
        "danse",
        "dance",
        "langue",
        "language",
        "adult",
        "adultes",
        "formation",
        "professionnelle",
        "professionnel",
        "metier",
        "metiers",
    ]
    if any(marker in blob for marker in exclusion_markers):
        return None

    secondary_markers = [
        "secondaire",
        "high school",
        "polyvalente",
        "sec.",
        "sec ",
        "isced:level 2",
        "isced:level 3",
        "grade 7",
        "grade 8",
        "grade 9",
        "grade 10",
        "grade 11",
        "grade 12",
    ]
    if any(marker in blob for marker in secondary_markers):
        return "secondaire"

    primary_markers = [
        "primaire",
        "elementary",
        "elementaire",
        "isced:level 1",
        "grade 1",
        "grade 2",
        "grade 3",
        "grade 4",
        "grade 5",
        "grade 6",
    ]
    if any(marker in blob for marker in primary_markers):
        return "primaire"

    try:
        max_age = int(float(tags.get("max_age")))
        if max_age <= 12:
            return "primaire"
        if max_age >= 13:
            return "secondaire"
    except (TypeError, ValueError):
        pass

    return "primaire"


def _is_duplicate_service(existing: dict, candidate: dict, category: str) -> bool:
    """Deduplication plus fine que 'nom uniquement' pour ne pas perdre des chaines distinctes."""
    distance_km = _haversine(existing["lat"], existing["lon"], candidate["lat"], candidate["lon"])
    existing_name = _normalize_service_name(existing.get("nom", ""))
    candidate_name = _normalize_service_name(candidate.get("nom", ""))

    if category == "bus":
        if existing_name and candidate_name and existing_name == candidate_name and distance_km <= 0.25:
            return True
        return distance_km <= 0.09

    if existing_name and candidate_name and existing_name == candidate_name and distance_km <= 0.12:
        return True

    if (not existing_name or not candidate_name) and distance_km <= 0.05:
        return True

    return False


def _empty_services_dict() -> Dict[str, list]:
    return {
        "epicerie": [],
        "primaire": [],
        "secondaire": [],
        "cegep": [],
        "universite": [],
        "pharmacie": [],
        "bus": [],
        "parc": [],
        "loisir": [],
        "restaurant": [],
        "essence": [],
    }


def _tomtom_search_poi(
    query: str,
    lat: float,
    lon: float,
    rayon: int,
    limit: int = 12,
    brand_set: Optional[str] = None,
) -> List[dict]:
    data = _tomtom_get(
        f"/search/2/poiSearch/{quote(query, safe='')}.json",
        params={
            "lat": lat,
            "lon": lon,
            "radius": rayon,
            "limit": limit,
            "countrySet": TOMTOM_COUNTRYSET,
            "language": TOMTOM_LANGUAGE,
            "relatedPois": "off",
            "brandSet": brand_set,
        },
        timeout=8,
    )
    return data.get("results", [])


def _tomtom_result_name(result: dict) -> str:
    poi = result.get("poi", {}) or {}
    name = poi.get("name", "")
    if name:
        return name

    brands = poi.get("brands") or []
    if brands:
        first_brand = brands[0] or {}
        if isinstance(first_brand, dict):
            return first_brand.get("name", "")
        return str(first_brand)

    address = result.get("address", {}) or {}
    return address.get("freeformAddress", "")


def _tomtom_result_blob(result: dict) -> str:
    """Assemble les champs utiles TomTom pour filtrer les faux positifs."""
    poi = result.get("poi", {}) or {}
    parts = [_tomtom_result_name(result)]

    for category in poi.get("categories") or []:
        parts.append(str(category))

    for classification in poi.get("classifications") or []:
        parts.append(str(classification.get("code", "")))
        for name_info in classification.get("names") or []:
            parts.append(str(name_info.get("name", "")))

    for brand in poi.get("brands") or []:
        if isinstance(brand, dict):
            parts.append(str(brand.get("name", "")))
        else:
            parts.append(str(brand))

    return " ".join(_normalize_service_name(part) for part in parts if part)


def _is_specialty_food_place(name: str) -> bool:
    """Exclut les commerces alimentaires trop specialises de la categorie epicerie."""
    blob = _normalize_service_name(name)
    exclusion_markers = [
        "restaurant",
        "resto",
        "cafe",
        "café",
        "bistro",
        "brasserie",
        "pizzeria",
        "sushi",
        "cremerie",
        "crémerie",
        "creamery",
        "ice cream",
        "glacier",
        "gelato",
        "yogourt glace",
        "yogourt glacé",
        "fromagerie",
        "boucherie",
        "poissonnerie",
        "boulangerie",
        "patisserie",
        "pâtisserie",
        "saucissier",
        "fruiterie",
        "marche public",
        "marché public",
        "eau pure",
        "depanneur",
        "dépanneur",
        "convenience",
    ]
    return any(marker in blob for marker in exclusion_markers)


def _tomtom_matches_expected_category(category: str, result: dict) -> bool:
    blob = _tomtom_result_blob(result)
    name_blob = _normalize_service_name(_tomtom_result_name(result))

    if category == "epicerie":
        is_core_grocery = any(
            marker in blob
            for marker in [
                "supermarket",
                "supermarkets hypermarkets",
                "food drinks: grocers",
                "grocer",
                "grocery",
                "iga",
                "metro",
                "super c",
                "maxi",
                "provigo",
                "adonis",
                "costco",
            ]
        )
        return is_core_grocery and not _is_specialty_food_place(name_blob)

    if category == "pharmacie":
        return any(
            marker in blob
            for marker in [
                "pharmacy",
                "familiprix",
                "jean coutu",
                "uniprix",
                "pharmaprix",
                "brunet",
                "proxim",
            ]
        )

    if category == "primaire":
        return (
            "primary school" in blob
            or "elementary school" in blob
            or ("ecole" in blob and "secondaire" not in blob)
            or ("école" in blob and "secondaire" not in blob)
        )

    if category == "secondaire":
        return any(marker in blob for marker in ["high school", "secondary school", "polyvalente", "secondaire"])

    if category == "cegep":
        return any(marker in name_blob for marker in ["cegep", "cégep", "college", "collège"])

    if category == "universite":
        return any(marker in name_blob for marker in ["universite", "université", "university", "campus", "faculty", "faculte", "faculté"])

    if category == "bus":
        return any(marker in blob for marker in ["bus stop", "bus station", "transit", "public transport", "gare routiere", "gare routière"])

    if category == "parc":
        return any(marker in blob for marker in ["park", "playground", "garden", "parc"])

    return True


def _tomtom_build_info(result: dict, origin_lat: float, origin_lon: float, default_name: str) -> Optional[dict]:
    position = result.get("position", {}) or {}
    lat = position.get("lat")
    lon = position.get("lon")
    if lat is None or lon is None:
        return None

    name = _tomtom_result_name(result) or default_name
    return {
        "nom": name,
        "lat": float(lat),
        "lon": float(lon),
        "distance_km": _haversine(origin_lat, origin_lon, float(lat), float(lon)),
        "temps_min": max(1, round((_haversine(origin_lat, origin_lon, float(lat), float(lon)) / 40) * 60)),
    }


def _tomtom_route_metrics(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> Tuple[float, int]:
    fallback_dist = _haversine(origin_lat, origin_lon, dest_lat, dest_lon)
    fallback_time = max(1, round((fallback_dist / 40) * 60))

    try:
        route_key = f"{origin_lat:.6f},{origin_lon:.6f}:{dest_lat:.6f},{dest_lon:.6f}"
        data = _tomtom_get(
            f"/routing/1/calculateRoute/{route_key}/json",
            params={
                "travelMode": "car",
                "routeType": "fastest",
                "traffic": "false",
                "language": TOMTOM_LANGUAGE,
            },
            timeout=8,
        )
        summary = ((data.get("routes") or [{}])[0]).get("summary", {})
        length_m = summary.get("lengthInMeters")
        travel_s = summary.get("travelTimeInSeconds")
        if not length_m or not travel_s:
            return fallback_dist, fallback_time
        return round(length_m / 1000, 2), max(1, round(travel_s / 60))
    except Exception:
        return fallback_dist, fallback_time


def _merge_service_candidates(base_services: Dict[str, list], incoming_services: Dict[str, list], max_per_category: int) -> Dict[str, list]:
    merged = _empty_services_dict()
    for category in merged:
        combined = []
        for source in (base_services.get(category, []), incoming_services.get(category, [])):
            for candidate in source:
                if not any(_is_duplicate_service(existing, candidate, category) for existing in combined):
                    combined.append(candidate)
        combined.sort(key=lambda item: (item.get("temps_min", 9999), item.get("distance_km", 9999)))
        merged[category] = combined[:max_per_category]
    return merged


def _obtenir_tous_services_tomtom(lat: float, lon: float, rayon: int = 5000) -> Dict[str, list]:
    """Recherche de services proches via TomTom Search + vrais temps via Routing."""
    services = _empty_services_dict()
    query_map = {
        "epicerie": [
            {"query": "supermarket", "brand_set": "IGA,Metro,Super C,Maxi,Provigo,Adonis,Walmart,Costco"},
            {"query": "grocery store"},
            {"query": "epicerie"},
        ],
        "primaire": [
            {"query": "primary school"},
            {"query": "elementary school"},
            {"query": "ecole primaire"},
        ],
        "secondaire": [
            {"query": "secondary school"},
            {"query": "high school"},
            {"query": "ecole secondaire"},
        ],
        "cegep": [
            {"query": "cegep"},
            {"query": "cégep"},
        ],
        "universite": [
            {"query": "university"},
            {"query": "universite"},
        ],
        "pharmacie": [
            {"query": "pharmacy", "brand_set": "Jean Coutu,Uniprix,Pharmaprix,Brunet,Familiprix,Proxim"},
            {"query": "pharmacie"},
        ],
        "bus": [
            {"query": "bus stop"},
            {"query": "bus station"},
        ],
        "parc": [
            {"query": "park"},
            {"query": "parc"},
            {"query": "playground"},
        ],
    }
    default_labels = {
        "epicerie": "Epicerie",
        "primaire": "Ecole primaire",
        "secondaire": "Ecole secondaire",
        "cegep": "Cegep / College",
        "universite": "Universite",
        "pharmacie": "Pharmacie",
        "bus": "Arret de bus",
        "parc": "Parc",
    }

    for category, searches in query_map.items():
        candidates = []
        for search_cfg in searches:
            results = _tomtom_search_poi(
                search_cfg["query"],
                lat=lat,
                lon=lon,
                rayon=rayon,
                limit=10 if category == "bus" else 8,
                brand_set=search_cfg.get("brand_set"),
            )
            for result in results:
                if not _tomtom_matches_expected_category(category, result):
                    continue
                info = _tomtom_build_info(result, lat, lon, default_labels[category])
                if not info:
                    continue
                if not any(_is_duplicate_service(existing, info, category) for existing in candidates):
                    candidates.append(info)

        candidates.sort(key=lambda item: item["distance_km"])
        shortlisted = candidates[:TOMTOM_ROUTE_CANDIDATES]

        enriched = []
        for info in shortlisted:
            route_distance_km, route_time_min = _tomtom_route_metrics(lat, lon, info["lat"], info["lon"])
            info["distance_km"] = route_distance_km
            info["temps_min"] = route_time_min
            enriched.append(info)

        enriched.sort(key=lambda item: (item["temps_min"], item["distance_km"]))
        services[category] = enriched[:TOMTOM_MAX_RESULTS_PER_CATEGORY]

    return services


def _obtenir_tous_services_overpass(lat: float, lon: float, rayon: int = 5000) -> Dict[str, list]:
    """
    Trouve TOUS les services dans un rayon donné via Overpass, triés par distance.
    Retourne un dictionnaire avec une liste de services par catégorie.
    """
    query = f"""
    [out:json][timeout:35];
    (
      node["highway"="bus_stop"](around:{rayon},{lat},{lon});
      node["amenity"="bus_station"](around:{rayon},{lat},{lon});
      way["amenity"="bus_station"](around:{rayon},{lat},{lon});
      node["amenity"~"school|college|university"](around:{rayon},{lat},{lon});
      way["amenity"~"school|college|university"](around:{rayon},{lat},{lon});
      relation["amenity"~"school|college|university"](around:{rayon},{lat},{lon});
      node["shop"~"supermarket|greengrocer|grocery"](around:{rayon},{lat},{lon});
      way["shop"~"supermarket|greengrocer|grocery"](around:{rayon},{lat},{lon});
      relation["shop"~"supermarket|greengrocer|grocery"](around:{rayon},{lat},{lon});
      node["amenity"="pharmacy"](around:{rayon},{lat},{lon});
      node["shop"="chemist"](around:{rayon},{lat},{lon});
      way["amenity"="pharmacy"](around:{rayon},{lat},{lon});
      way["shop"="chemist"](around:{rayon},{lat},{lon});
      node["healthcare"="pharmacy"](around:{rayon},{lat},{lon});
      way["healthcare"="pharmacy"](around:{rayon},{lat},{lon});
      relation["amenity"="pharmacy"](around:{rayon},{lat},{lon});
      relation["shop"="chemist"](around:{rayon},{lat},{lon});
      relation["healthcare"="pharmacy"](around:{rayon},{lat},{lon});
      node["leisure"~"park|playground|garden|sports_centre|ice_rink|swimming_pool|pitch"](around:{rayon},{lat},{lon});
      way["leisure"~"park|playground|garden|sports_centre|ice_rink|swimming_pool|pitch"](around:{rayon},{lat},{lon});
      node["amenity"~"cinema|restaurant|fast_food|cafe|fuel"](around:{rayon},{lat},{lon});
      way["amenity"~"cinema|restaurant|fast_food|cafe|fuel"](around:{rayon},{lat},{lon});
    );
    out center tags;
    """
    
    services = _empty_services_dict()
    
    try:
        urls = [
            "https://overpass-api.de/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter",
            "https://z.overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"
        ]
        
        data = None
        for url in urls:
            try:
                response = requests.post(url, data={"data": query}, timeout=25)
                if response.status_code == 200 and 'application/json' in response.headers.get('content-type', ''):
                    data = response.json()
                    break
            except Exception:
                pass
            time.sleep(1)
        
        if not data:
            print(f"Overpass n'a pas répondu correctement")
            return services
        
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            el_lat = el.get('lat') or (el.get('center', {}).get('lat'))
            el_lon = el.get('lon') or (el.get('center', {}).get('lon'))
            if not el_lat or not el_lon:
                continue
            
            nom = tags.get('name', '')
            dist_km = _haversine(lat, lon, el_lat, el_lon)
            # Estimation du temps en voiture (~40 km/h en ville, minimum 1 min)
            temps_min = max(1, round((dist_km / 40) * 60))
            
            info = {
                "nom": nom,
                "lat": el_lat,
                "lon": el_lon,
                "distance_km": dist_km,
                "temps_min": temps_min
            }
            
            if tags.get("highway") == "bus_stop" or tags.get("amenity") == "bus_station":
                info["nom"] = nom or "Arret de bus"
                services["bus"].append(info)
            elif tags.get("amenity") in ["school", "college", "university"]:
                bucket = _infer_school_bucket(tags, nom)
                if bucket == "primaire":
                    info["nom"] = nom or "Ecole primaire"
                    services["primaire"].append(info)
                elif bucket == "secondaire":
                    info["nom"] = nom or "Ecole secondaire"
                    services["secondaire"].append(info)
                elif bucket == "cegep":
                    info["nom"] = nom or "Cegep / College"
                    services["cegep"].append(info)
                elif bucket == "universite":
                    info["nom"] = nom or "Universite"
                    services["universite"].append(info)
            elif _is_grocery_store(tags, nom):
                info["nom"] = nom or "Epicerie"
                services["epicerie"].append(info)
            elif _is_pharmacy(tags, nom):
                info["nom"] = nom or "Pharmacie"
                services["pharmacie"].append(info)
            elif tags.get("leisure") in ["park", "playground", "garden"]:
                info["nom"] = nom or "Parc"
                services["parc"].append(info)
            elif tags.get("amenity") == "cinema" or tags.get("leisure") in ["sports_centre", "ice_rink", "swimming_pool", "pitch"]:
                info["nom"] = nom or "Loisir / Centre sportif"
                services["loisir"].append(info)
            elif tags.get("amenity") in ["restaurant", "fast_food", "cafe"]:
                info["nom"] = nom or "Restaurant / Café"
                services["restaurant"].append(info)
            elif tags.get("amenity") == "fuel":
                info["nom"] = nom or "Station-service"
                services["essence"].append(info)
        
        # Trier chaque catégorie par distance et dédupliquer par nom
        for cat in services:
            services[cat].sort(key=lambda x: x['distance_km'])
            dedup = []
            for s in services[cat]:
                if not any(_is_duplicate_service(existing, s, cat) for existing in dedup):
                    dedup.append(s)
            services[cat] = dedup

    except Exception as e:
        print(f"Erreur d'analyse proximite Overpass: {e}")
        
    return services


def obtenir_tous_services(lat: float, lon: float, rayon: int = 5000) -> Dict[str, list]:
    """
    Recherche les services proches en privilégiant TomTom.
    Les structures de sortie restent identiques pour l'UI actuelle.
    """
    if _tomtom_enabled():
        try:
            services_tomtom = _obtenir_tous_services_tomtom(lat, lon, rayon=rayon)
            services_overpass = _obtenir_tous_services_overpass(lat, lon, rayon=rayon)
            return _merge_service_candidates(
                services_tomtom,
                services_overpass,
                max_per_category=TOMTOM_MAX_RESULTS_PER_CATEGORY,
            )
        except Exception as e:
            print(f"TomTom obtenir_tous_services indisponible, fallback Overpass: {e}")

    return _obtenir_tous_services_overpass(lat, lon, rayon=rayon)



def obtenir_loisirs_ville(ville: str, lat: float, lon: float) -> dict:
    """
    Compte les restaurants, loisirs et stations-service dans les limites EXACTES
    de la municipalite via son relation-ID OSM (obtenu depuis Nominatim).
    Fallback sur rayon 5 km si la relation OSM est introuvable.
    """
    headers = {"User-Agent": USER_AGENT}
    urls_overpass = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    # Etape 1 : obtenir l ID OSM de la municipalite via Nominatim
    osm_area_id = None
    methode = f"rayon 5 km autour de l adresse (limite OSM introuvable pour {ville})"

    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{ville}, Quebec, Canada",
                "format": "json",
                "addressdetails": 1,
                "limit": 5,
                "featuretype": "city",
            },
            headers=headers,
            timeout=8,
        )
        r.raise_for_status()
        time.sleep(0.5)

        for res in r.json():
            osm_type = res.get("osm_type", "")
            osm_id   = int(res.get("osm_id", 0))
            addr     = res.get("address", {})
            # Verifier que c est bien au Quebec et une relation (polygone)
            if addr.get("state") in ("Quebec", "Québec") and osm_type == "relation" and osm_id > 0:
                # Overpass area ID = relation ID + 3 600 000 000
                osm_area_id = osm_id + 3_600_000_000
                methode = f"limites municipales OSM ({ville})"
                break
    except Exception:
        pass

    # Etape 2 : requete Overpass dans le polygone exact
    if osm_area_id:
        query = f"""
[out:json][timeout:40];
area({osm_area_id})->.mun;
(
  node["amenity"~"restaurant|fast_food|cafe|bar|pub|food_court|ice_cream"](area.mun);
  way["amenity"~"restaurant|fast_food|cafe|bar|pub|food_court|ice_cream"](area.mun);
  node["amenity"="cinema"](area.mun);
  node["leisure"~"sports_centre|ice_rink|swimming_pool|arena"](area.mun);
  way["leisure"~"sports_centre|ice_rink|swimming_pool|arena"](area.mun);
  node["amenity"="fuel"](area.mun);
  way["amenity"="fuel"](area.mun);
);
out center tags;
"""
    else:
        rayon = 5000
        query = f"""
[out:json][timeout:40];
(
  node["amenity"~"restaurant|fast_food|cafe|bar|pub|food_court|ice_cream"](around:{rayon},{lat},{lon});
  way["amenity"~"restaurant|fast_food|cafe|bar|pub|food_court|ice_cream"](around:{rayon},{lat},{lon});
  node["amenity"="cinema"](around:{rayon},{lat},{lon});
  node["leisure"~"sports_centre|ice_rink|swimming_pool|arena"](around:{rayon},{lat},{lon});
  way["leisure"~"sports_centre|ice_rink|swimming_pool|arena"](around:{rayon},{lat},{lon});
  node["amenity"="fuel"](around:{rayon},{lat},{lon});
  way["amenity"="fuel"](around:{rayon},{lat},{lon});
);
out center tags;
"""

    nb_restos = nb_loisirs = nb_essence = 0

    for url in urls_overpass:
        try:
            resp = requests.post(url, data={"data": query}, timeout=45)
            if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
                ids_vus = set()

                for el in resp.json().get("elements", []):
                    el_id   = el.get("id", 0)
                    # Dédupliquer par ID OSM unique (évite node+way du même lieu)
                    if el_id in ids_vus:
                        continue
                    ids_vus.add(el_id)

                    tags    = el.get("tags", {})
                    amenity = tags.get("amenity", "")
                    leisure = tags.get("leisure", "")

                    if amenity in ("restaurant", "fast_food", "cafe"):
                        nb_restos += 1
                    elif amenity == "cinema" or leisure in ("sports_centre", "ice_rink", "swimming_pool", "arena"):
                        nb_loisirs += 1
                    elif amenity == "fuel":
                        nb_essence += 1
                break  # succes
        except Exception:
            pass
        time.sleep(0.5)

    return {
        "nb_restos":  nb_restos,
        "nb_loisirs": nb_loisirs,
        "nb_essence": nb_essence,
        "methode":    methode,
    }

