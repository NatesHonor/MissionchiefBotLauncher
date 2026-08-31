"""Blue-first visual themes shared by every launcher surface."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    background: str
    surface: str
    surface_alt: str
    border: str
    text: str
    muted: str
    primary: str
    primary_hover: str
    cyan: str
    success: str
    danger: str


THEMES = {
    "ocean": Theme("Ocean Blue", "#07111F", "#0B1B2D", "#102640", "#1D3B5B", "#EAF4FF", "#7F9DB8", "#2583E8", "#4BA3FF", "#27C4E8", "#35D399", "#F06B7A"),
    "midnight": Theme("Midnight Blue", "#050B16", "#091426", "#0D1E35", "#183453", "#E6F1FF", "#7890AD", "#1D65D8", "#3B82F6", "#21B8D4", "#2DD4A1", "#F87171"),
    "arctic": Theme("Arctic Blue", "#07151D", "#0B222E", "#103344", "#21536A", "#ECFBFF", "#86AEBE", "#0B9BD7", "#32B9E8", "#2DD4BF", "#34D399", "#FB7185"),
    "cobalt": Theme("Cobalt", "#07101F", "#0A1830", "#10244A", "#25477F", "#F0F6FF", "#91A8C8", "#3B6FF5", "#628BFF", "#37BDF8", "#4ADE80", "#FB7185"),
}


def theme_names():
    return list(THEMES.keys())


def theme_label(name: str) -> str:
    return THEMES.get(name, THEMES["ocean"]).name


def current_theme_name(value: str | None) -> str:
    return value if value in THEMES else "ocean"


def stylesheet(theme_name: str = "ocean") -> str:
    theme = THEMES.get(theme_name, THEMES["ocean"])
    return f"""
    * {{ font-family: 'Segoe UI'; color: {theme.text}; }}
    QMainWindow#MissionHelperWindow {{ background: {theme.background}; }}
    QFrame#Root, QFrame#TopBar, QFrame#Sidebar, QFrame#Card, QFrame#HeroCard, QFrame#StatusCard,
    QFrame#WebCard, QFrame#SettingsCard, QFrame#ProfileCard {{ background: {theme.surface}; border: 1px solid {theme.border}; border-radius: 14px; }}
    QFrame#TopBar {{ border-radius: 0; border-left: 0; border-right: 0; border-top: 0; background: {theme.background}; }}
    QFrame#Sidebar {{ border-radius: 0; border-left: 0; border-top: 0; border-bottom: 0; background: {theme.surface}; }}
    QScrollArea#DashboardScroll, QScrollArea#SettingsScroll {{ background: {theme.background}; border: 0; }}
    QWidget#DashboardPage, QWidget#SettingsPage {{ background: transparent; }}
    QLabel#BrandMark {{ background: {theme.primary}; color: white; border-radius: 10px; font-size: 14px; font-weight: 800; padding: 7px 8px; }}
    QLabel#BrandTitle {{ color: {theme.text}; font-size: 14px; font-weight: 700; }}
    QLabel#ConnectionLabel {{ color: {theme.success}; font-size: 11px; font-weight: 600; }}
    QLabel#CardTitle {{ color: {theme.text}; font-size: 15px; font-weight: 700; }}
    QLabel#StatusBadge {{ color: {theme.cyan}; background: {theme.surface_alt}; border: 1px solid {theme.border}; border-radius: 9px; padding: 3px 8px; font-size: 10px; font-weight: 700; }}
    QLabel#Avatar, QLabel#SettingsAvatar {{ background: {theme.surface_alt}; color: {theme.cyan}; border: 1px solid {theme.primary}; border-radius: 30px; font-size: 18px; font-weight: 700; }}
    QFrame#UpdateCard {{ background: {theme.surface_alt}; border: 1px solid {theme.border}; border-radius: 11px; }}
    QLabel#UpdateTitle {{ color: {theme.text}; font-size: 11px; font-weight: 700; }}
    QLabel#UpdateTitle[available="true"] {{ color: {theme.cyan}; }}
    QLabel#FooterLabel {{ color: {theme.muted}; font-size: 10px; }}
    QLabel#StatusDot {{ color: {theme.success}; }}
    QDialog#RegionDialog {{ background: {theme.surface}; border: 1px solid {theme.border}; border-radius: 14px; }}
    QFrame#DialogHeader {{ background: {theme.surface_alt}; border-bottom: 1px solid {theme.border}; }}
    QLabel#DialogTitle {{ color: {theme.text}; font-size: 13px; font-weight: 700; }}
    QScrollArea#RegionList {{ background: {theme.background}; border: 1px solid {theme.border}; border-radius: 10px; padding: 6px; }}
    QPushButton#SecondaryButton[current="true"] {{ background: {theme.surface_alt}; border-color: {theme.cyan}; color: {theme.text}; }}
    QWebEngineView#MissionChiefView {{ background: {theme.background}; border: 0; border-radius: 10px; }}
    QLabel#PageTitle {{ font-size: 20px; font-weight: 700; color: {theme.text}; }}
    QLabel#Eyebrow {{ color: {theme.cyan}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }}
    QLabel#Muted, QLabel#Hint {{ color: {theme.muted}; }}
    QLabel#HeroTitle {{ font-size: 27px; font-weight: 700; color: {theme.text}; }}
    QLabel#HeroCopy {{ color: {theme.muted}; font-size: 13px; }}
    QLabel#StatValue {{ color: {theme.text}; font-size: 21px; font-weight: 700; }}
    QLabel#StatLabel {{ color: {theme.muted}; font-size: 11px; }}
    QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 9px 12px; color: {theme.muted}; text-align: left; }}
    QPushButton:hover {{ background: {theme.surface_alt}; color: {theme.text}; border-color: {theme.border}; }}
    QPushButton:disabled {{ color: {theme.muted}; }}
    QPushButton#NavButton {{ font-size: 13px; font-weight: 600; padding: 11px 13px; }}
    QPushButton#NavButton[active="true"] {{ color: {theme.text}; background: {theme.surface_alt}; border-color: {theme.primary}; }}
    QPushButton#PrimaryButton {{ background: {theme.primary}; color: white; border: 0; font-size: 13px; font-weight: 700; padding: 11px 18px; }}
    QPushButton#PrimaryButton:hover {{ background: {theme.primary_hover}; }}
    QPushButton#DangerButton {{ background: {theme.danger}; color: white; border: 0; font-size: 13px; font-weight: 700; padding: 11px 18px; }}
    QPushButton#SecondaryButton {{ background: {theme.surface_alt}; border-color: {theme.border}; color: {theme.text}; }}
    QPushButton#IconButton {{ font-size: 15px; padding: 6px; border-radius: 8px; }}
    QPushButton#CloseButton:hover {{ background: {theme.danger}; color: white; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{ background: {theme.background}; border: 1px solid {theme.border}; border-radius: 9px; padding: 9px 10px; color: {theme.text}; selection-background-color: {theme.primary}; }}
    QComboBox::drop-down {{ border: 0; width: 24px; }}
    QComboBox QAbstractItemView {{ background: {theme.surface}; color: {theme.text}; selection-background-color: {theme.primary}; border: 1px solid {theme.border}; }}
    QPlainTextEdit#ConsoleOutput {{ font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 12px; padding: 12px; }}
    QProgressBar {{ background: {theme.background}; border: 0; border-radius: 4px; height: 7px; text-align: center; }}
    QProgressBar::chunk {{ background: {theme.primary}; border-radius: 4px; }}
    QScrollBar:vertical {{ background: transparent; width: 7px; margin: 3px; }}
    QScrollBar::handle:vertical {{ background: {theme.border}; border-radius: 3px; min-height: 30px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """
