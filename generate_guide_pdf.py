from __future__ import annotations

from math import ceil
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageColor, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
PAGES_DIR = DOCS_DIR / "guide_pages"
OUTPUT_PDF = DOCS_DIR / "guide_application_rentabilite_immobiliere.pdf"
OUTPUT_PREVIEW = DOCS_DIR / "guide_application_rentabilite_immobiliere_preview.png"
LOGO_PATH = ROOT / "imvest_logo.png"

PAGE_W = 1240
PAGE_H = 1754
MARGIN = 84
CONTENT_W = PAGE_W - (MARGIN * 2)
TOTAL_PAGES = 8

COLORS = {
    "navy": "#002A54",
    "blue": "#005A9C",
    "gold": "#FFC000",
    "bg": "#F4F6F9",
    "card": "#FFFFFF",
    "line": "#D9E2EC",
    "text": "#1E293B",
    "muted": "#64748B",
    "green": "#16A34A",
    "orange": "#D97706",
    "red": "#DC2626",
    "teal": "#0F766E",
    "sky": "#EAF3FB",
    "gold_soft": "#FFF7DA",
    "green_soft": "#EAF8EF",
    "red_soft": "#FDECEC",
    "blue_soft": "#EEF4FB",
}


def rgb(color: str) -> tuple[int, int, int]:
    return ImageColor.getrgb(color)


def rgba(color: str, alpha: int) -> tuple[int, int, int, int]:
    return (*rgb(color), alpha)


def font_candidates(style: str) -> list[Path]:
    windows_fonts = Path("C:/Windows/Fonts")
    mapping = {
        "regular": [windows_fonts / "segoeui.ttf", windows_fonts / "arial.ttf"],
        "semibold": [windows_fonts / "seguisb.ttf", windows_fonts / "arialbd.ttf"],
        "bold": [windows_fonts / "segoeuib.ttf", windows_fonts / "arialbd.ttf"],
    }
    return mapping[style]


def load_font(size: int, style: str = "regular") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in font_candidates(style):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


FONTS = {
    "title": load_font(54, "bold"),
    "subtitle": load_font(24, "regular"),
    "section": load_font(34, "bold"),
    "h3": load_font(24, "bold"),
    "body": load_font(19, "regular"),
    "body_bold": load_font(19, "semibold"),
    "small": load_font(16, "regular"),
    "small_bold": load_font(16, "semibold"),
    "badge": load_font(15, "semibold"),
    "step": load_font(28, "bold"),
    "quote": load_font(28, "bold"),
}

MEASURE_DRAW = ImageDraw.Draw(Image.new("RGB", (32, 32), "#FFFFFF"))


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def line_height(font: ImageFont.ImageFont) -> int:
    left, top, right, bottom = font.getbbox("Ag")
    return bottom - top


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        width, _ = text_size(draw, test, font)
        if width <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_lines(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    fill: str,
    gap: int = 8,
) -> int:
    current_y = y
    lh = line_height(font)
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += lh + gap
    return current_y


def draw_paragraph(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    width: int,
    font: ImageFont.ImageFont,
    fill: str,
    gap: int = 8,
) -> int:
    return draw_lines(draw, wrap_text(draw, text, font, width), x, y, font, fill, gap)


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    items: Iterable[str],
    x: int,
    y: int,
    width: int,
    font: ImageFont.ImageFont,
    fill: str,
    bullet_fill: str,
) -> int:
    current_y = y
    for item in items:
        bullet_y = current_y + 9
        draw.ellipse((x, bullet_y, x + 10, bullet_y + 10), fill=bullet_fill)
        lines = wrap_text(draw, item, font, width - 28)
        current_y = draw_lines(draw, lines, x + 24, current_y, font, fill, gap=6) + 8
    return current_y


def text_block_height(text: str, font: ImageFont.ImageFont, width: int, gap: int = 8) -> int:
    lines = wrap_text(MEASURE_DRAW, text, font, width)
    if not lines:
        return 0
    return len(lines) * line_height(font) + max(0, len(lines) - 1) * gap


def bullets_block_height(items: list[str], font: ImageFont.ImageFont, width: int) -> int:
    total = 0
    for item in items:
        lines = wrap_text(MEASURE_DRAW, item, font, width - 28)
        if lines:
            total += len(lines) * line_height(font) + max(0, len(lines) - 1) * 6 + 8
    return total


def estimate_panel_height(width: int, body: str = "", bullets: list[str] | None = None) -> int:
    inner_width = width - 48
    total = 122
    if body:
        total += text_block_height(body, FONTS["body"], inner_width, gap=6) + 12
    if bullets:
        total += bullets_block_height(bullets, FONTS["body"], inner_width)
    return total + 22


def round_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str | None = None,
    width: int = 2,
    radius: int = 28,
    shadow: bool = True,
) -> None:
    x1, y1, x2, y2 = box
    if shadow:
        draw.rounded_rectangle(
            (x1 + 8, y1 + 10, x2 + 8, y2 + 10),
            radius=radius,
            fill=rgba("#0F172A", 18),
        )
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def pill(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    fill: str,
    text_fill: str,
    font: ImageFont.ImageFont = FONTS["badge"],
) -> int:
    text_w, text_h = text_size(draw, text, font)
    pad_x = 18
    pad_y = 10
    box = (x, y, x + text_w + (pad_x * 2), y + text_h + (pad_y * 2))
    draw.rounded_rectangle(box, radius=24, fill=fill)
    draw.text((x + pad_x, y + pad_y - 1), text, font=font, fill=text_fill)
    return box[2] - box[0]


def add_background(page_num: int, section_title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    base = Image.new("RGBA", (PAGE_W, PAGE_H), COLORS["bg"])
    overlay = Image.new("RGBA", (PAGE_W, PAGE_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    od.rectangle((0, 0, PAGE_W, 250), fill=COLORS["navy"])
    od.ellipse((PAGE_W - 320, -130, PAGE_W + 140, 300), fill=rgba(COLORS["gold"], 62))
    od.ellipse((-170, PAGE_H - 240, 250, PAGE_H + 120), fill=rgba(COLORS["blue"], 22))
    od.rounded_rectangle((MARGIN, 190, PAGE_W - MARGIN, PAGE_H - 92), radius=38, fill=rgba("#FFFFFF", 242))

    page = Image.alpha_composite(base, overlay).convert("RGB")
    draw = ImageDraw.Draw(page)

    title_x = MARGIN
    title_top_y = 92
    title_max_width = PAGE_W - (MARGIN * 2) - 120
    title_lines = wrap_text(draw, section_title, FONTS["section"], title_max_width)
    title_height = len(title_lines) * line_height(FONTS["section"]) + max(0, len(title_lines) - 1) * 4
    subtitle_height = line_height(FONTS["small"])
    title_block_height = title_height + 6 + subtitle_height

    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo.thumbnail((200, 74))
        logo_box = (MARGIN - 8, 34, MARGIN + logo.width + 8, 34 + logo.height + 14)
        draw.rounded_rectangle(logo_box, radius=22, fill=rgba("#FFFFFF", 236))
        page.paste(logo, (MARGIN, 41), logo)
        title_x = logo_box[2] + 28
        title_max_width = PAGE_W - title_x - MARGIN
        title_lines = wrap_text(draw, section_title, FONTS["section"], title_max_width)
        title_height = len(title_lines) * line_height(FONTS["section"]) + max(0, len(title_lines) - 1) * 4
        title_block_height = title_height + 6 + subtitle_height
        logo_center_y = (logo_box[1] + logo_box[3]) / 2
        title_top_y = int(logo_center_y - (title_block_height / 2))

    subtitle_y = draw_lines(draw, title_lines, title_x, title_top_y, FONTS["section"], "#FFFFFF", gap=4) + 6
    draw.text((title_x, subtitle_y), subtitle, font=FONTS["small"], fill=rgba("#FFFFFF", 225))

    footer_text = f"Guide explicatif  |  Page {page_num}/{TOTAL_PAGES}"
    footer_w, _ = text_size(draw, footer_text, FONTS["small"])
    draw.text((PAGE_W - MARGIN - footer_w, PAGE_H - 58), footer_text, font=FONTS["small"], fill=COLORS["muted"])

    return page, draw


def draw_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    body: str = "",
    bullets: list[str] | None = None,
    accent: str = COLORS["blue"],
    fill: str = COLORS["card"],
    title_fill: str = COLORS["navy"],
    body_fill: str = COLORS["text"],
    shadow: bool = False,
) -> int:
    round_box(draw, box, fill, outline=COLORS["line"], shadow=shadow)
    x1, y1, x2, _ = box
    draw.rounded_rectangle((x1 + 24, y1 + 22, x1 + 92, y1 + 28), radius=3, fill=accent)
    title_y = y1 + 42
    draw.text((x1 + 24, title_y), title, font=FONTS["h3"], fill=title_fill)
    current_y = title_y + 46
    if body:
        current_y = draw_paragraph(draw, body, x1 + 24, current_y, x2 - x1 - 48, FONTS["body"], body_fill, gap=6) + 12
    if bullets:
        current_y = draw_bullets(draw, bullets, x1 + 24, current_y, x2 - x1 - 48, FONTS["body"], body_fill, accent)
    return current_y


def draw_quote_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    quote: str,
    accent: str,
    label: str,
) -> None:
    round_box(draw, box, COLORS["navy"], shadow=False)
    x1, y1, x2, _ = box
    pill(draw, x1 + 24, y1 + 22, label, accent, COLORS["navy"])
    draw_paragraph(draw, quote, x1 + 24, y1 + 78, x2 - x1 - 48, FONTS["quote"], "#FFFFFF", gap=6)


def draw_kpi_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    note: str,
    accent: str,
    fill: str,
) -> None:
    round_box(draw, box, fill, outline=accent, shadow=False, radius=24)
    x1, y1, x2, _ = box
    draw.text((x1 + 20, y1 + 18), label, font=FONTS["small_bold"], fill=COLORS["navy"])
    value_font = FONTS["section"] if len(value) <= 8 else FONTS["step"]
    draw.text((x1 + 20, y1 + 52), value, font=value_font, fill=accent)
    _, value_h = text_size(draw, value, value_font)
    note_y = y1 + 52 + value_h + 12
    draw_paragraph(draw, note, x1 + 20, note_y, x2 - x1 - 40, FONTS["small"], COLORS["text"], gap=4)


def cover_page() -> Image.Image:
    page = Image.new("RGBA", (PAGE_W, PAGE_H), COLORS["bg"])
    overlay = Image.new("RGBA", (PAGE_W, PAGE_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    od.rectangle((0, 0, PAGE_W, 540), fill=COLORS["navy"])
    od.ellipse((PAGE_W - 260, -150, PAGE_W + 120, 230), fill=rgba(COLORS["gold"], 82))
    od.ellipse((-200, 1060, 320, 1540), fill=rgba(COLORS["blue"], 26))
    od.rounded_rectangle((MARGIN, 430, PAGE_W - MARGIN, PAGE_H - 96), radius=42, fill=rgba("#FFFFFF", 244))

    page = Image.alpha_composite(page, overlay).convert("RGB")
    draw = ImageDraw.Draw(page)

    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo.thumbnail((300, 110))
        logo_box = (MARGIN - 12, 30, MARGIN + logo.width + 12, 30 + logo.height + 18)
        draw.rounded_rectangle(logo_box, radius=24, fill=rgba("#FFFFFF", 236))
        page.paste(logo, (MARGIN, 38), logo)

    title_text = "Guide de l'application\nd'analyse de rentabilité immobilière"
    draw.multiline_text(
        (MARGIN, 160),
        title_text,
        font=FONTS["title"],
        fill="#FFFFFF",
        spacing=8,
    )
    draw.text(
        (MARGIN, 318),
        "Un guide pas-a-pas pour comprendre l'outil et arriver plus vite a une decision.",
        font=FONTS["subtitle"],
        fill=rgba("#FFFFFF", 230),
    )

    intro = (
        "L'application sert a analyser rapidement un immeuble locatif et a transformer les "
        "chiffres en lecture claire. Son objectif est simple : aider a decider d'un achat "
        "immobilier avec plus de structure et moins d'incertitude."
    )
    draw_paragraph(draw, intro, MARGIN + 40, 478, 930, FONTS["body"], COLORS["text"], gap=7)

    journey_box = (MARGIN + 40, 620, PAGE_W - MARGIN - 40, 940)
    round_box(draw, journey_box, COLORS["blue_soft"], outline=COLORS["line"], shadow=False)
    draw.text((journey_box[0] + 24, journey_box[1] + 22), "Le parcours suivi dans le guide", font=FONTS["h3"], fill=COLORS["navy"])

    steps = [
        ("1", "Entrer les données", COLORS["blue"]),
        ("2", "Voir les résultats", COLORS["orange"]),
        ("3", "Analyser", COLORS["teal"]),
        ("4", "Décider", COLORS["green"]),
    ]
    node_y = journey_box[1] + 84
    node_w = 204
    gap = 22
    inner_width = journey_box[2] - journey_box[0] - 48
    total_row_width = len(steps) * node_w + (len(steps) - 1) * gap
    visual_center_bias = 28
    start_x = journey_box[0] + 24 + max(0, (inner_width - total_row_width) // 2) + visual_center_bias
    for index, (number, label, accent) in enumerate(steps):
        x1 = start_x + index * (node_w + gap)
        x2 = x1 + node_w
        round_box(draw, (x1, node_y, x2, node_y + 116), COLORS["card"], outline=COLORS["line"], shadow=False, radius=24)
        chip_box = (x1 + 18, node_y + 18, x1 + 68, node_y + 68)
        draw.rounded_rectangle(chip_box, radius=16, fill=accent)
        num_w, num_h = text_size(draw, number, FONTS["step"])
        chip_cx = (chip_box[0] + chip_box[2]) / 2
        chip_cy = (chip_box[1] + chip_box[3]) / 2
        draw.text((chip_cx - num_w / 2, chip_cy - num_h / 2 - 1), number, font=FONTS["step"], fill="#FFFFFF")
        draw_paragraph(draw, label, x1 + 84, node_y + 30, 96, FONTS["small_bold"], COLORS["navy"], gap=4)
        if index < len(steps) - 1:
            line_x = x2 + 8
            mid_y = node_y + 58
            draw.line((line_x, mid_y, line_x + 12, mid_y), fill=COLORS["muted"], width=3)
            draw.polygon([(line_x + 12, mid_y), (line_x + 4, mid_y - 5), (line_x + 4, mid_y + 5)], fill=COLORS["muted"])

    draw_paragraph(
        draw,
        "Le document suit exactement la logique de l'application : on saisit les donnees, on lit les resultats, on analyse le dossier, puis on passe a l'action.",
        journey_box[0] + 24,
        journey_box[1] + 236,
        journey_box[2] - journey_box[0] - 48,
        FONTS["body"],
        COLORS["text"],
        gap=6,
    )

    objective_box = (MARGIN + 40, 980, PAGE_W - MARGIN - 40, 1180)
    round_box(draw, objective_box, COLORS["navy"], shadow=False)
    pill(draw, objective_box[0] + 24, objective_box[1] + 22, "Objectif", COLORS["gold"], COLORS["navy"])
    draw_paragraph(
        draw,
        "Le but n'est pas de produire plus d'analyse. Le but est d'aider l'utilisateur a comprendre rapidement comment utiliser l'application du debut a la fin et a poser une decision plus solide.",
        objective_box[0] + 24,
        objective_box[1] + 78,
        objective_box[2] - objective_box[0] - 48,
        FONTS["body"],
        "#FFFFFF",
        gap=6,
    )

    learn_box = (MARGIN + 40, 1230, PAGE_W - MARGIN - 40, 1490)
    round_box(draw, learn_box, COLORS["card"], outline=COLORS["line"], shadow=False)
    draw.text((learn_box[0] + 24, learn_box[1] + 24), "Ce que l'utilisateur doit retenir apres lecture", font=FONTS["h3"], fill=COLORS["navy"])
    draw_bullets(
        draw,
        [
            "Quelles donnees entrer et pourquoi cette premiere etape est critique.",
            "Comment lire les indicateurs sans se perdre dans les ratios.",
            "Comment transformer les resultats en decision concrete : acheter, negocier ou refuser.",
        ],
        learn_box[0] + 24,
        learn_box[1] + 80,
        learn_box[2] - learn_box[0] - 48,
        FONTS["body"],
        COLORS["text"],
        COLORS["gold"],
    )

    footer_text = f"Guide explicatif  |  Page 1/{TOTAL_PAGES}"
    footer_w, _ = text_size(draw, footer_text, FONTS["small"])
    draw.text((PAGE_W - MARGIN - footer_w, PAGE_H - 58), footer_text, font=FONTS["small"], fill=COLORS["muted"])
    return page


def page_step1() -> Image.Image:
    page, draw = add_background(2, "Étape 1 - Entrer les données", "Section 1 : Informations sur l'immeuble")
    intro = (
        "Cette premiere etape pose toute la base du dossier. Plus les informations entrees sont "
        "realistes, plus l'analyse financiere et la recommandation seront utiles."
    )
    draw_paragraph(draw, intro, MARGIN + 34, 286, CONTENT_W - 68, FONTS["body"], COLORS["text"], gap=6)

    left_body = "L'application attend les informations qui structurent un immeuble a revenus :"
    left_bullets = [
        "Prix d'achat.",
        "Mise de fonds.",
        "Revenus locatifs.",
        "Depenses annuelles.",
        "Financement : taux, amortissement et structure du pret.",
    ]
    right_bullets = [
        "Le prix d'achat influence directement le rendement du projet.",
        "La mise de fonds change le poids de la dette et la marge de securite.",
        "Les loyers et les depenses determinent si l'immeuble respire ou etouffe.",
        "Le financement modifie le cashflow, le CSD et la lecture du risque.",
    ]
    panel_w = 514
    top_y = 386
    top_h = max(
        estimate_panel_height(panel_w, left_body, left_bullets),
        estimate_panel_height(panel_w, "", right_bullets),
    )
    quote_y = top_y + top_h + 36
    quote_h = 164
    closing_y = quote_y + quote_h + 34
    closing_h = estimate_panel_height(
        PAGE_W - (MARGIN * 2) - 68,
        "A cette etape, l'utilisateur ne cherche pas encore a conclure. Il cherche surtout a fiabiliser son point de depart.",
        [
            "Verifier que les loyers saisis sont realistes.",
            "Ne pas sous-estimer les depenses recurrentes.",
            "Utiliser un scenario de financement proche de la realite.",
        ],
    )

    draw_panel(
        draw,
        (MARGIN + 34, top_y, MARGIN + 548, top_y + top_h),
        "Ce que l'utilisateur doit entrer",
        left_body,
        left_bullets,
        accent=COLORS["blue"],
        fill=COLORS["blue_soft"],
    )

    draw_panel(
        draw,
        (MARGIN + 572, top_y, PAGE_W - MARGIN - 34, top_y + top_h),
        "Pourquoi c'est important",
        "",
        right_bullets,
        accent=COLORS["orange"],
        fill=COLORS["card"],
    )

    draw_quote_box(
        draw,
        (MARGIN + 34, quote_y, PAGE_W - MARGIN - 34, quote_y + quote_h),
        "La qualité des résultats dépend directement de la qualité des données entrées.",
        COLORS["gold"],
        "Point critique",
    )

    draw_panel(
        draw,
        (MARGIN + 34, closing_y, PAGE_W - MARGIN - 34, closing_y + closing_h),
        "Lecture utile avant de continuer",
        "A cette etape, l'utilisateur ne cherche pas encore a conclure. Il cherche surtout a fiabiliser son point de depart.",
        [
            "Verifier que les loyers saisis sont realistes.",
            "Ne pas sous-estimer les depenses recurrentes.",
            "Utiliser un scenario de financement proche de la realite.",
        ],
        accent=COLORS["teal"],
        fill=COLORS["card"],
    )
    return page


def page_step2() -> Image.Image:
    page, draw = add_background(3, "Étape 2 - Comprendre les calculs", "Section 2 : Analyse financiere et ratios")
    quote_y = 286
    quote_h = 144
    draw_quote_box(
        draw,
        (MARGIN + 34, quote_y, PAGE_W - MARGIN - 34, quote_y + quote_h),
        "On commence par le cashflow et le CSD, puis on valide avec le cap rate, le TRI et la VAN.",
        COLORS["gold"],
        "Logique de lecture",
    )

    top_cards = [
        (
            (MARGIN + 34, 484, MARGIN + 346, 760),
            "Cashflow",
            "Premiere question : est-ce que le projet s'autofinance ?",
            ["Positif : l'immeuble couvre mieux ses charges.", "Negatif : l'investisseur doit remettre de l'argent."],
            COLORS["green"],
            COLORS["green_soft"],
        ),
        (
            (MARGIN + 364, 484, MARGIN + 676, 760),
            "CSD",
            "Deuxieme question : est-ce que la dette est securitaire ?",
            ["Plus il est eleve, plus la couverture de la dette est confortable.", "Un CSD faible signale un montage plus fragile."],
            COLORS["blue"],
            COLORS["blue_soft"],
        ),
        (
            (MARGIN + 694, 484, PAGE_W - MARGIN - 34, 760),
            "Cap rate",
            "Il mesure le rendement de l'immeuble avant le financement.",
            ["Il aide a juger si le prix paye est coherent.", "C'est un bon filtre pour comparer plusieurs dossiers."],
            COLORS["orange"],
            COLORS["gold_soft"],
        ),
    ]
    top_y = quote_y + quote_h + 38
    small_w = 312
    top_h = max(
        estimate_panel_height(small_w, top_cards[0][2], top_cards[0][3]),
        estimate_panel_height(small_w, top_cards[1][2], top_cards[1][3]),
        estimate_panel_height(small_w, top_cards[2][2], top_cards[2][3]),
    )
    top_cards = [
        ((MARGIN + 34, top_y, MARGIN + 346, top_y + top_h), *top_cards[0][1:]),
        ((MARGIN + 364, top_y, MARGIN + 676, top_y + top_h), *top_cards[1][1:]),
        ((MARGIN + 694, top_y, PAGE_W - MARGIN - 34, top_y + top_h), *top_cards[2][1:]),
    ]
    for box, title, body, bullets, accent, fill in top_cards:
        draw_panel(draw, box, title, body, bullets, accent=accent, fill=fill)

    bottom_cards = [
        (
            (MARGIN + 34, 796, MARGIN + 548, 1078),
            "TRI",
            "Le TRI donne une lecture du rendement global du projet sur l'horizon d'investissement.",
            ["Il combine cashflow, equite et sortie.", "Il est utile pour comparer des projets de nature differente."],
            COLORS["navy"],
            COLORS["card"],
        ),
        (
            (MARGIN + 572, 796, PAGE_W - MARGIN - 34, 1078),
            "VAN",
            "La VAN indique si l'investissement cree vraiment de la valeur au taux de rendement exige.",
            ["Positive : le projet depasse le rendement minimal vise.", "Negative : le projet ne cree pas assez de valeur."],
            COLORS["teal"],
            COLORS["card"],
        ),
    ]
    bottom_y = top_y + top_h + 34
    wide_h = max(
        estimate_panel_height(514, bottom_cards[0][2], bottom_cards[0][3]),
        estimate_panel_height(514, bottom_cards[1][2], bottom_cards[1][3]),
    )
    bottom_cards = [
        ((MARGIN + 34, bottom_y, MARGIN + 548, bottom_y + wide_h), *bottom_cards[0][1:]),
        ((MARGIN + 572, bottom_y, PAGE_W - MARGIN - 34, bottom_y + wide_h), *bottom_cards[1][1:]),
    ]
    for box, title, body, bullets, accent, fill in bottom_cards:
        draw_panel(draw, box, title, body, bullets, accent=accent, fill=fill)

    summary_y = bottom_y + wide_h + 34
    summary_h = estimate_panel_height(
        PAGE_W - (MARGIN * 2) - 68,
        "La bonne lecture est progressive :",
        [
            "1. Cashflow : verifier si l'immeuble respire des maintenant.",
            "2. CSD : verifier si la dette reste supportable.",
            "3. Cap rate : juger le rendement de l'actif lui-meme.",
            "4. TRI et VAN : confirmer l'interet global du projet a moyen terme.",
        ],
    )

    draw_panel(
        draw,
        (MARGIN + 34, summary_y, PAGE_W - MARGIN - 34, summary_y + summary_h),
        "Comment lire cette section sans se perdre",
        "La bonne lecture est progressive :",
        [
            "1. Cashflow : verifier si l'immeuble respire des maintenant.",
            "2. CSD : verifier si la dette reste supportable.",
            "3. Cap rate : juger le rendement de l'actif lui-meme.",
            "4. TRI et VAN : confirmer l'interet global du projet a moyen terme.",
        ],
        accent=COLORS["gold"],
        fill=COLORS["card"],
    )
    return page


def page_step3() -> Image.Image:
    page, draw = add_background(4, "Étape 3 - Analyse de la localisation", "Section 3 : Localisation et environnement")
    intro = (
        "Un bon rendement sur papier ne suffit pas. L'emplacement influence la vacance, la stabilite "
        "des loyers et le potentiel du projet dans le temps."
    )
    draw_paragraph(draw, intro, MARGIN + 34, 286, CONTENT_W - 68, FONTS["body"], COLORS["text"], gap=6)

    draw_quote_box(
        draw,
        (MARGIN + 34, 372, PAGE_W - MARGIN - 34, 516),
        "Un bon immeuble dans un mauvais secteur reste un mauvais investissement.",
        COLORS["gold"],
        "Pourquoi cette étape compte",
    )

    cards = [
        (
            (MARGIN + 34, 574, MARGIN + 346, 938),
            "Proximité des services",
            "L'application regarde si le bien est bien relie a son environnement quotidien.",
            ["Services utiles a proximite.", "Acces plus simple pour les locataires.", "Valeur pratique du secteur."],
            COLORS["blue"],
            COLORS["blue_soft"],
        ),
        (
            (MARGIN + 364, 574, MARGIN + 676, 938),
            "Qualité du secteur",
            "On cherche un quartier coherent avec une demande locative stable.",
            ["Lecture globale de l'emplacement.", "Confort de vie et attractivite.", "Marge de securite locative."],
            COLORS["teal"],
            COLORS["card"],
        ),
        (
            (MARGIN + 694, 574, PAGE_W - MARGIN - 34, 938),
            "Potentiel du marché",
            "L'application complete la lecture immediate par une vision du potentiel du secteur.",
            ["Dynamique locale.", "Capacite a soutenir les loyers.", "Potentiel de revente ou d'appreciation."],
            COLORS["orange"],
            COLORS["gold_soft"],
        ),
    ]
    row_y = 574
    row_h = max(
        estimate_panel_height(312, cards[0][2], cards[0][3]),
        estimate_panel_height(312, cards[1][2], cards[1][3]),
        estimate_panel_height(312, cards[2][2], cards[2][3]),
    )
    cards = [
        ((MARGIN + 34, row_y, MARGIN + 346, row_y + row_h), *cards[0][1:]),
        ((MARGIN + 364, row_y, MARGIN + 676, row_y + row_h), *cards[1][1:]),
        ((MARGIN + 694, row_y, PAGE_W - MARGIN - 34, row_y + row_h), *cards[2][1:]),
    ]
    for box, title, body, bullets, accent, fill in cards:
        draw_panel(draw, box, title, body, bullets, accent=accent, fill=fill)

    final_y = row_y + row_h + 36
    final_h = estimate_panel_height(
        PAGE_W - (MARGIN * 2) - 68,
        "La section localisation ne remplace pas une visite ni une validation terrain. Elle sert a completer la lecture financiere par une lecture de contexte.",
        [
            "Un immeuble rentable dans un secteur faible peut devenir plus risqué qu'il n'y parait.",
            "Un secteur solide peut justifier une lecture plus favorable a condition que les chiffres suivent.",
            "L'objectif est de juger le projet dans son ensemble, pas seulement dans un tableur.",
        ],
    )

    draw_panel(
        draw,
        (MARGIN + 34, final_y, PAGE_W - MARGIN - 34, final_y + final_h),
        "Ce que l'utilisateur doit retenir",
        "La section localisation ne remplace pas une visite ni une validation terrain. Elle sert a completer la lecture financiere par une lecture de contexte.",
        [
            "Un immeuble rentable dans un secteur faible peut devenir plus risqué qu'il n'y parait.",
            "Un secteur solide peut justifier une lecture plus favorable a condition que les chiffres suivent.",
            "L'objectif est de juger le projet dans son ensemble, pas seulement dans un tableur.",
        ],
        accent=COLORS["green"],
        fill=COLORS["card"],
    )
    return page


def page_step4() -> Image.Image:
    page, draw = add_background(5, "Étape 4 - Interprétation et recommandation", "Section 4 : Résumé, verdict et plan d'action")
    intro = (
        "Cette section transforme les chiffres en lecture utilisable. L'application resume le dossier, "
        "signale les forces et les points faibles, puis propose un verdict lisible."
    )
    draw_paragraph(draw, intro, MARGIN + 34, 286, CONTENT_W - 68, FONTS["body"], COLORS["text"], gap=6)

    cards = [
        (
            (MARGIN + 34, 396, MARGIN + 548, 714),
            "Résumé automatique",
            "Une synthese rapide permet de comprendre la these generale du dossier sans relire tous les chiffres.",
            ["Vue d'ensemble.", "Lecture rapide.", "Priorisation des points importants."],
            COLORS["blue"],
            COLORS["blue_soft"],
        ),
        (
            (MARGIN + 572, 396, PAGE_W - MARGIN - 34, 714),
            "Verdict",
            "Le verdict aide a formuler la conclusion : acheter, negocier ou refuser.",
            ["Decision plus lisible.", "Prise de recul rapide.", "Signal de prudence ou d'ouverture."],
            COLORS["green"],
            COLORS["green_soft"],
        ),
        (
            (MARGIN + 34, 742, MARGIN + 548, 1060),
            "Forces et points faibles",
            "L'application montre ce qui soutient le dossier et ce qui le fragilise.",
            ["Forces a proteger.", "Faiblesses a corriger.", "Marge de securite a surveiller."],
            COLORS["orange"],
            COLORS["gold_soft"],
        ),
        (
            (MARGIN + 572, 742, PAGE_W - MARGIN - 34, 1060),
            "Plan d'action",
            "La recommandation ne s'arrete pas au verdict. Elle propose des leviers concrets.",
            ["Ajuster le prix.", "Revoir la mise de fonds.", "Travailler les loyers ou les hypothèses."],
            COLORS["teal"],
            COLORS["card"],
        ),
    ]
    row1_y = 396
    row1_h = max(
        estimate_panel_height(514, cards[0][2], cards[0][3]),
        estimate_panel_height(514, cards[1][2], cards[1][3]),
    )
    row2_y = row1_y + row1_h + 32
    row2_h = max(
        estimate_panel_height(514, cards[2][2], cards[2][3]),
        estimate_panel_height(514, cards[3][2], cards[3][3]),
    )
    cards = [
        ((MARGIN + 34, row1_y, MARGIN + 548, row1_y + row1_h), *cards[0][1:]),
        ((MARGIN + 572, row1_y, PAGE_W - MARGIN - 34, row1_y + row1_h), *cards[1][1:]),
        ((MARGIN + 34, row2_y, MARGIN + 548, row2_y + row2_h), *cards[2][1:]),
        ((MARGIN + 572, row2_y, PAGE_W - MARGIN - 34, row2_y + row2_h), *cards[3][1:]),
    ]
    for box, title, body, bullets, accent, fill in cards:
        draw_panel(draw, box, title, body, bullets, accent=accent, fill=fill)

    final_y = row2_y + row2_h + 36
    final_h = estimate_panel_height(
        PAGE_W - (MARGIN * 2) - 68,
        "",
        [
            "Cashflow négatif + CSD faible : projet risqué.",
            "Cashflow limite : projet à optimiser avant d'avancer.",
            "Cashflow positif + bons ratios : projet intéressant à confirmer.",
        ],
    )

    draw_panel(
        draw,
        (MARGIN + 34, final_y, PAGE_W - MARGIN - 34, final_y + final_h),
        "Lecture rapide pour conclure",
        "",
        [
            "Cashflow négatif + CSD faible : projet risqué.",
            "Cashflow limite : projet à optimiser avant d'avancer.",
            "Cashflow positif + bons ratios : projet intéressant à confirmer.",
        ],
        accent=COLORS["red"],
        fill=COLORS["card"],
    )
    return page


def page_step5() -> Image.Image:
    page, draw = add_background(6, "Étape 5 - Passer à la décision", "Transformer les résultats en action")
    quote_y = 286
    quote_h = 144
    draw_quote_box(
        draw,
        (MARGIN + 34, quote_y, PAGE_W - MARGIN - 34, quote_y + quote_h),
        "L'objectif n'est pas d'analyser, mais de décider.",
        COLORS["gold"],
        "Message clé",
    )

    left_body = "L'utilisateur doit chercher des leviers avant d'aller plus loin."
    left_bullets = [
        "Négocier le prix.",
        "Augmenter la mise de fonds.",
        "Revoir les loyers, les dépenses ou les hypothèses.",
    ]
    right_body = "Le bon réflexe n'est pas de foncer. Il faut confirmer."
    right_bullets = [
        "Valider les hypothèses une dernière fois.",
        "Confirmer les données avec le terrain et le financement réel.",
        "S'assurer que les chiffres affichés correspondent au marché.",
    ]
    top_y = quote_y + quote_h + 42
    top_h = max(
        estimate_panel_height(514, left_body, left_bullets),
        estimate_panel_height(514, right_body, right_bullets),
    )
    final_y = top_y + top_h + 36
    final_h = estimate_panel_height(
        PAGE_W - (MARGIN * 2) - 68,
        "",
        [
            "Le prix demandé est-il encore cohérent après lecture complète du dossier ?",
            "Les loyers et les coûts sont-ils appuyés par des données réelles ?",
            "Le projet reste-t-il solide si un paramètre devient un peu moins favorable ?",
        ],
    )

    draw_panel(
        draw,
        (MARGIN + 34, top_y, MARGIN + 548, top_y + top_h),
        "Si le projet est risqué",
        left_body,
        left_bullets,
        accent=COLORS["red"],
        fill=COLORS["red_soft"],
    )

    draw_panel(
        draw,
        (MARGIN + 572, top_y, PAGE_W - MARGIN - 34, top_y + top_h),
        "Si le projet est intéressant",
        right_body,
        right_bullets,
        accent=COLORS["green"],
        fill=COLORS["green_soft"],
    )

    draw_panel(
        draw,
        (MARGIN + 34, final_y, PAGE_W - MARGIN - 34, final_y + final_h),
        "Questions finales avant d'avancer",
        "",
        [
            "Le prix demandé est-il encore cohérent après lecture complète du dossier ?",
            "Les loyers et les coûts sont-ils appuyés par des données réelles ?",
            "Le projet reste-t-il solide si un paramètre devient un peu moins favorable ?",
        ],
        accent=COLORS["blue"],
        fill=COLORS["card"],
    )
    return page


def page_example() -> Image.Image:
    page, draw = add_background(7, "Exemple concret", "Un mini cas pour lire l'application rapidement")
    intro = "Voici un exemple simple pour montrer comment les indicateurs mènent a une conclusion concrete."
    draw_paragraph(draw, intro, MARGIN + 34, 286, CONTENT_W - 68, FONTS["body"], COLORS["text"], gap=6)

    case_box = (MARGIN + 34, 372, PAGE_W - MARGIN - 34, 652)
    round_box(draw, case_box, COLORS["card"], outline=COLORS["line"], shadow=False)
    draw.text((case_box[0] + 24, case_box[1] + 24), "Mini cas", font=FONTS["h3"], fill=COLORS["navy"])

    kpi_y = case_box[1] + 88
    card_h = 150
    draw_kpi_card(draw, (case_box[0] + 24, kpi_y, case_box[0] + 334, kpi_y + card_h), "Prix", "350 000$", "Prix d'achat du projet.", COLORS["blue"], COLORS["blue_soft"])
    draw_kpi_card(draw, (case_box[0] + 358, kpi_y, case_box[0] + 668, kpi_y + card_h), "Cashflow", "-300$/mois", "L'investisseur doit remettre de l'argent chaque mois.", COLORS["red"], COLORS["red_soft"])
    draw_kpi_card(draw, (case_box[0] + 692, kpi_y, case_box[2] - 24, kpi_y + card_h), "CSD", "0.85", "La dette est mal couverte.", COLORS["orange"], COLORS["gold_soft"])

    flow_boxes = [
        (
            (MARGIN + 34, 680, MARGIN + 346, 1038),
            "Lecture 1",
            "Le cashflow est negatif.",
            ["Le projet ne s'autofinance pas.", "Le proprietaire doit combler le manque chaque mois."],
            COLORS["red"],
            COLORS["red_soft"],
        ),
        (
            (MARGIN + 364, 680, MARGIN + 676, 1038),
            "Lecture 2",
            "Le CSD de 0.85 reste trop faible.",
            ["La couverture de la dette est insuffisante.", "Le dossier manque de marge de securite."],
            COLORS["orange"],
            COLORS["gold_soft"],
        ),
        (
            (MARGIN + 694, 680, PAGE_W - MARGIN - 34, 1038),
            "Conclusion",
            "Le projet est fragile dans sa forme actuelle.",
            ["Une négociation est nécessaire.", "Le dossier doit être ajusté avant d'aller plus loin."],
            COLORS["navy"],
            COLORS["card"],
        ),
    ]
    flow_y = 716
    flow_h = max(
        estimate_panel_height(312, flow_boxes[0][2], flow_boxes[0][3]),
        estimate_panel_height(312, flow_boxes[1][2], flow_boxes[1][3]),
        estimate_panel_height(312, flow_boxes[2][2], flow_boxes[2][3]),
    )
    flow_boxes = [
        ((MARGIN + 34, flow_y, MARGIN + 346, flow_y + flow_h), *flow_boxes[0][1:]),
        ((MARGIN + 364, flow_y, MARGIN + 676, flow_y + flow_h), *flow_boxes[1][1:]),
        ((MARGIN + 694, flow_y, PAGE_W - MARGIN - 34, flow_y + flow_h), *flow_boxes[2][1:]),
    ]
    for box, title, body, bullets, accent, fill in flow_boxes:
        draw_panel(draw, box, title, body, bullets, accent=accent, fill=fill)

    quote_y = flow_y + flow_h + 38
    quote_h = 170
    closing_y = quote_y + quote_h + 34
    closing_h = estimate_panel_height(
        PAGE_W - (MARGIN * 2) - 68,
        "Il montre comment passer d'un chiffre isole a une decision simple et actionnable.",
        [
            "Le cashflow signale le manque de souffle.",
            "Le CSD confirme le risque sur la dette.",
            "Le verdict oriente l'utilisateur vers la négociation.",
        ],
    )

    draw_quote_box(
        draw,
        (MARGIN + 34, quote_y, PAGE_W - MARGIN - 34, quote_y + quote_h),
        "Conclusion : projet fragile → négociation nécessaire",
        COLORS["gold"],
        "Lecture finale",
    )

    draw_panel(
        draw,
        (MARGIN + 34, closing_y, PAGE_W - MARGIN - 34, closing_y + closing_h),
        "Pourquoi cet exemple aide",
        "Il montre comment passer d'un chiffre isole a une decision simple et actionnable.",
        [
            "Le cashflow signale le manque de souffle.",
            "Le CSD confirme le risque sur la dette.",
            "Le verdict oriente l'utilisateur vers la négociation.",
        ],
        accent=COLORS["teal"],
        fill=COLORS["card"],
    )
    return page


def page_limits_conclusion() -> Image.Image:
    page, draw = add_background(8, "Limites, bonnes pratiques et conclusion", "Garder le bon niveau de prudence")

    left_body = "L'application aide a structurer une decision, mais elle ne remplace pas la realite du terrain."
    left_bullets = [
        "Les résultats sont des estimations.",
        "Ils dépendent directement des hypothèses entrées.",
        "Une hypothèse erronée peut modifier fortement la conclusion.",
        "Le marché réel est plus important que les projections.",
    ]
    right_body = "Avant de prendre une decision finale, l'utilisateur doit valider le dossier dans le monde reel."
    right_bullets = [
        "Vérifier le marché locatif local.",
        "Confirmer les coûts réels et les travaux.",
        "Tester un financement réaliste.",
        "Comparer plus d'un scénario si le projet est limite.",
    ]
    top_y = 286
    top_h = max(
        estimate_panel_height(514, left_body, left_bullets),
        estimate_panel_height(514, right_body, right_bullets),
    )
    quote_y = top_y + top_h + 42
    quote_h = 164
    closing_y = quote_y + quote_h + 38
    closing_h = estimate_panel_height(
        PAGE_W - (MARGIN * 2) - 68,
        "Après lecture, l'utilisateur doit être capable de :",
        [
            "Comprendre comment lire les résultats.",
            "Comprendre comment prendre une décision.",
            "Identifier les actions concrètes à poser ensuite.",
        ],
    )

    draw_panel(
        draw,
        (MARGIN + 34, top_y, MARGIN + 548, top_y + top_h),
        "Limites à garder en tête",
        left_body,
        left_bullets,
        accent=COLORS["red"],
        fill=COLORS["card"],
    )

    draw_panel(
        draw,
        (MARGIN + 572, top_y, PAGE_W - MARGIN - 34, top_y + top_h),
        "Bonnes pratiques",
        right_body,
        right_bullets,
        accent=COLORS["blue"],
        fill=COLORS["blue_soft"],
    )

    draw_quote_box(
        draw,
        (MARGIN + 34, quote_y, PAGE_W - MARGIN - 34, quote_y + quote_h),
        "Le marché réel est plus important que les projections.",
        COLORS["gold"],
        "Bonne pratique",
    )

    draw_panel(
        draw,
        (MARGIN + 34, closing_y, PAGE_W - MARGIN - 34, closing_y + closing_h),
        "Conclusion",
        "Après lecture, l'utilisateur doit être capable de :",
        [
            "Comprendre comment lire les résultats.",
            "Comprendre comment prendre une décision.",
            "Identifier les actions concrètes à poser ensuite.",
        ],
        accent=COLORS["green"],
        fill=COLORS["green_soft"],
    )
    return page


def create_preview(pages: list[Image.Image]) -> Image.Image:
    thumb_w = 332
    thumb_h = int(PAGE_H * (thumb_w / PAGE_W))
    gap = 32
    rows = ceil(len(pages) / 2)
    preview_w = gap + (thumb_w + gap) * 2
    preview_h = gap + (thumb_h + 72 + gap) * rows
    preview = Image.new("RGB", (preview_w, preview_h), "#EEF2F7")
    draw = ImageDraw.Draw(preview)

    for idx, page in enumerate(pages):
        thumb = page.copy()
        thumb.thumbnail((thumb_w, thumb_h))
        col = idx % 2
        row = idx // 2
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + 72 + gap)
        draw.rounded_rectangle((x - 6, y - 6, x + thumb_w + 6, y + thumb_h + 54), radius=24, fill="#FFFFFF", outline=COLORS["line"], width=2)
        preview.paste(thumb, (x, y))
        draw.text((x, y + thumb_h + 18), f"Page {idx + 1}", font=FONTS["small_bold"], fill=COLORS["navy"])
    return preview


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    pages = [
        cover_page(),
        page_step1(),
        page_step2(),
        page_step3(),
        page_step4(),
        page_step5(),
        page_example(),
        page_limits_conclusion(),
    ]

    for index, page in enumerate(pages, start=1):
        page.save(PAGES_DIR / f"page_{index}.png", quality=95)

    pages[0].save(
        OUTPUT_PDF,
        save_all=True,
        append_images=pages[1:],
        resolution=150.0,
    )

    create_preview(pages).save(OUTPUT_PREVIEW, quality=95)
    print(f"PDF généré : {OUTPUT_PDF}")
    print(f"Aperçu généré : {OUTPUT_PREVIEW}")


if __name__ == "__main__":
    main()
