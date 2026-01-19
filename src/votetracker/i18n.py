"""
Internationalization (i18n) module for VoteTracker.
Supports English and Italian translations.
"""

import locale

# Current language
_current_lang = "en"

# Translations dictionary
TRANSLATIONS = {
    "en": {
        # Navigation
        "Dashboard": "Dashboard",
        "Votes": "Votes",
        "Subjects": "Subjects",
        "Simulator": "Simulator",
        "Calendar": "Calendar",
        "Report": "Report",
        "Statistics": "Statistics",
        "Settings": "Settings",

        # Common labels
        "Grade": "Grade",
        "Subject": "Subject",
        "Date": "Date",
        "Type": "Type",
        "Term": "Term",
        "Average": "Average",
        "Weight": "Weight",
        "Description": "Description",
        "Written": "Written",
        "Oral": "Oral",
        "Practical": "Practical",

        # Terms
        "1° Term": "1° Term",
        "2° Term": "2° Term",
        "Term 1": "Term 1",
        "Term 2": "Term 2",

        # Buttons
        "Add": "Add",
        "Edit": "Edit",
        "Delete": "Delete",
        "Save": "Save",
        "Cancel": "Cancel",
        "Close": "Close",
        "Export": "Export",
        "Import": "Import",
        "Add Vote": "Add Vote",
        "Add Subject": "Add Subject",
        "Get Started": "Get Started",

        # Dashboard
        "Overall Average": "Overall Average",
        "Total Votes": "Total Votes",
        "Failing": "Failing",
        "Subjects Overview": "Subjects Overview",
        "No votes recorded yet": "No votes recorded yet",
        "Quick Stats": "Quick Stats",
        "School Year": "School Year",

        # Votes page
        "Votes List": "Votes List",
        "Filter:": "Filter:",
        "All": "All",
        "Confirm Deletion": "Confirm Deletion",
        "Are you sure you want to delete this vote?": "Are you sure you want to delete this vote?",

        # Subjects page
        "votes": "votes",
        "vote": "vote",

        # Simulator
        "Target Average": "Target Average",
        "Calculate": "Calculate",
        "Grade Needed": "Grade Needed",
        "Vote Type": "Vote Type",
        "Both": "Both",
        "Oral only": "Oral only",
        "Written only": "Written only",
        "You need at least:": "You need at least:",
        "No votes yet": "No votes yet",
        "Select a subject": "Select a subject",
        "Target already reached": "Target already reached",
        "Impossible to reach": "Impossible to reach",

        # Calendar
        "Select a date": "Select a date",
        "No grades on this date": "No grades on this date",
        "Grades": "Grades",
        "Legend:": "Legend:",
        "Passing (6+)": "Passing (6+)",
        "Warning (5.5-6)": "Warning (5.5-6)",
        "Failing (<5.5)": "Failing (<5.5)",

        # Report Card
        "Report Card": "Report Card",
        "Export PDF": "Export PDF",
        "Final Grade": "Final Grade",
        "Proposed": "Proposed",
        "No subjects with grades": "No subjects with grades",

        # Statistics
        "Summary": "Summary",
        "Total Grades": "Total Grades",
        "Highest Grade": "Highest Grade",
        "Lowest Grade": "Lowest Grade",
        "Passing (>=6)": "Passing (>=6)",
        "Failing (<6)": "Failing (<6)",
        "Written Avg": "Written Avg",
        "Oral Avg": "Oral Avg",
        "Grade Distribution": "Grade Distribution",
        "Subject Averages": "Subject Averages",
        "Best Subjects": "Best Subjects",
        "Subjects to Improve": "Subjects to Improve",
        "No data": "No data",

        # Settings
        "Data Location": "Data Location",
        "School Years": "School Years",
        "Manage Years": "Manage Years",
        "Help": "Help",
        "Keyboard Shortcuts": "Keyboard Shortcuts",
        "Language": "Language",
        "Export to File": "Export to File",
        "Import from File": "Import from File",
        "Danger Zone": "Danger Zone",
        "Delete Current Term Votes": "Delete Current Term Votes",
        "Delete Current Year Votes": "Delete Current Year Votes",
        "Other": "Other",

        # Onboarding
        "Welcome to VoteTracker!": "Welcome to VoteTracker!",
        "Let's set up your grade tracker in a few simple steps.": "Let's set up your grade tracker in a few simple steps.",
        "Current school year:": "Current school year:",
        "You can manage school years later in Settings.": "You can manage school years later in Settings.",
        "Add Subjects": "Add Subjects",
        "Select the subjects you want to track:": "Select the subjects you want to track:",
        "Add custom subject...": "Add custom subject...",
        "Custom:": "Custom:",

        # Preset subjects (English)
        "Italian": "Italian",
        "Math": "Math",
        "English": "English",
        "History": "History",
        "Philosophy": "Philosophy",
        "Physics": "Physics",
        "Science": "Science",
        "Latin": "Latin",
        "Art": "Art",
        "Physical Education": "Physical Education",
        "Computer Science": "Computer Science",
        "Religion": "Religion",
        "Geography": "Geography",
        "Chemistry": "Chemistry",
        "Biology": "Biology",

        # Shortcuts help
        "Global": "Global",
        "Jump to page": "Jump to page",
        "Navigate pages": "Navigate pages",
        "Undo": "Undo",
        "Redo": "Redo",
        "Show this help": "Show this help",
        "Add new grade": "Add new grade",
        "Edit selected": "Edit selected",
        "Delete selected": "Delete selected",
        "Switch term": "Switch term",
        "Add new subject": "Add new subject",
        "Import data": "Import data",
        "Export data": "Export data",
        "Votes Page": "Votes Page",
        "Subjects Page": "Subjects Page",
        "Settings Page": "Settings Page",
        "Calendar / Report / Statistics": "Calendar / Report / Statistics",
        "Press ? or Esc to close": "Press ? or Esc to close",

        # Messages
        "year(s), active:": "year(s), active:",
        "Export Complete": "Export Complete",
        "Votes exported to:": "Votes exported to:",
        "Error": "Error",
        "Complete": "Complete",
    },
    "it": {
        # Navigation
        "Dashboard": "Dashboard",
        "Votes": "Voti",
        "Subjects": "Materie",
        "Simulator": "Simulatore",
        "Calendar": "Calendario",
        "Report": "Pagella",
        "Statistics": "Statistiche",
        "Settings": "Impostazioni",

        # Common labels
        "Grade": "Voto",
        "Subject": "Materia",
        "Date": "Data",
        "Type": "Tipo",
        "Term": "Quadrimestre",
        "Average": "Media",
        "Weight": "Peso",
        "Description": "Descrizione",
        "Written": "Scritto",
        "Oral": "Orale",
        "Practical": "Pratico",

        # Terms
        "1° Term": "1° Quadrimestre",
        "2° Term": "2° Quadrimestre",
        "Term 1": "Quadrimestre 1",
        "Term 2": "Quadrimestre 2",

        # Buttons
        "Add": "Aggiungi",
        "Edit": "Modifica",
        "Delete": "Elimina",
        "Save": "Salva",
        "Cancel": "Annulla",
        "Close": "Chiudi",
        "Export": "Esporta",
        "Import": "Importa",
        "Add Vote": "Aggiungi Voto",
        "Add Subject": "Aggiungi Materia",
        "Get Started": "Inizia",

        # Dashboard
        "Overall Average": "Media Generale",
        "Total Votes": "Voti Totali",
        "Failing": "Insufficienze",
        "Subjects Overview": "Panoramica Materie",
        "No votes recorded yet": "Nessun voto registrato",
        "Quick Stats": "Statistiche",
        "School Year": "Anno Scolastico",

        # Votes page
        "Votes List": "Lista Voti",
        "Filter:": "Filtra:",
        "All": "Tutti",
        "Confirm Deletion": "Conferma Eliminazione",
        "Are you sure you want to delete this vote?": "Sei sicuro di voler eliminare questo voto?",

        # Subjects page
        "votes": "voti",
        "vote": "voto",

        # Simulator
        "Target Average": "Media Obiettivo",
        "Calculate": "Calcola",
        "Grade Needed": "Voto Necessario",
        "Vote Type": "Tipo Voto",
        "Both": "Entrambi",
        "Oral only": "Solo orale",
        "Written only": "Solo scritto",
        "You need at least:": "Hai bisogno di almeno:",
        "No votes yet": "Nessun voto ancora",
        "Select a subject": "Seleziona una materia",
        "Target already reached": "Obiettivo già raggiunto",
        "Impossible to reach": "Impossibile da raggiungere",

        # Calendar
        "Select a date": "Seleziona una data",
        "No grades on this date": "Nessun voto in questa data",
        "Grades": "Voti",
        "Legend:": "Legenda:",
        "Passing (6+)": "Sufficiente (6+)",
        "Warning (5.5-6)": "Attenzione (5.5-6)",
        "Failing (<5.5)": "Insufficiente (<5.5)",

        # Report Card
        "Report Card": "Pagella",
        "Export PDF": "Esporta PDF",
        "Final Grade": "Voto Finale",
        "Proposed": "Proposto",
        "No subjects with grades": "Nessuna materia con voti",

        # Statistics
        "Summary": "Riepilogo",
        "Total Grades": "Voti Totali",
        "Highest Grade": "Voto Più Alto",
        "Lowest Grade": "Voto Più Basso",
        "Passing (>=6)": "Sufficienti (>=6)",
        "Failing (<6)": "Insufficienti (<6)",
        "Written Avg": "Media Scritti",
        "Oral Avg": "Media Orali",
        "Grade Distribution": "Distribuzione Voti",
        "Subject Averages": "Medie per Materia",
        "Best Subjects": "Materie Migliori",
        "Subjects to Improve": "Materie da Migliorare",
        "No data": "Nessun dato",

        # Settings
        "Data Location": "Posizione Dati",
        "School Years": "Anni Scolastici",
        "Manage Years": "Gestisci Anni",
        "Help": "Aiuto",
        "Keyboard Shortcuts": "Scorciatoie Tastiera",
        "Language": "Lingua",
        "Export to File": "Esporta su File",
        "Import from File": "Importa da File",
        "Danger Zone": "Zona Pericolosa",
        "Delete Current Term Votes": "Elimina Voti Quadrimestre",
        "Delete Current Year Votes": "Elimina Voti Anno",
        "Other": "Altro",

        # Onboarding
        "Welcome to VoteTracker!": "Benvenuto in VoteTracker!",
        "Let's set up your grade tracker in a few simple steps.": "Configuriamo il tuo registro voti in pochi semplici passi.",
        "Current school year:": "Anno scolastico corrente:",
        "You can manage school years later in Settings.": "Puoi gestire gli anni scolastici nelle Impostazioni.",
        "Add Subjects": "Aggiungi Materie",
        "Select the subjects you want to track:": "Seleziona le materie che vuoi tracciare:",
        "Add custom subject...": "Aggiungi materia personalizzata...",
        "Custom:": "Personalizzate:",

        # Preset subjects (Italian)
        "Italian": "Italiano",
        "Math": "Matematica",
        "English": "Inglese",
        "History": "Storia",
        "Philosophy": "Filosofia",
        "Physics": "Fisica",
        "Science": "Scienze",
        "Latin": "Latino",
        "Art": "Arte",
        "Physical Education": "Educazione Fisica",
        "Computer Science": "Informatica",
        "Religion": "Religione",
        "Geography": "Geografia",
        "Chemistry": "Chimica",
        "Biology": "Biologia",

        # Shortcuts help
        "Global": "Globali",
        "Jump to page": "Vai alla pagina",
        "Navigate pages": "Naviga pagine",
        "Undo": "Annulla",
        "Redo": "Ripeti",
        "Show this help": "Mostra questo aiuto",
        "Add new grade": "Aggiungi nuovo voto",
        "Edit selected": "Modifica selezionato",
        "Delete selected": "Elimina selezionato",
        "Switch term": "Cambia quadrimestre",
        "Add new subject": "Aggiungi nuova materia",
        "Import data": "Importa dati",
        "Export data": "Esporta dati",
        "Votes Page": "Pagina Voti",
        "Subjects Page": "Pagina Materie",
        "Settings Page": "Pagina Impostazioni",
        "Calendar / Report / Statistics": "Calendario / Pagella / Statistiche",
        "Press ? or Esc to close": "Premi ? o Esc per chiudere",

        # Messages
        "year(s), active:": "anno/i, attivo:",
        "Export Complete": "Esportazione Completata",
        "Votes exported to:": "Voti esportati in:",
        "Error": "Errore",
        "Complete": "Completato",
    }
}

# Preset subjects for onboarding (keys used for translation)
PRESET_SUBJECTS = [
    "Italian", "Math", "English", "History", "Philosophy",
    "Physics", "Science", "Latin", "Art", "Physical Education",
    "Computer Science", "Religion", "Geography", "Chemistry", "Biology"
]


def get_system_language() -> str:
    """Detect system language, return 'it' or 'en'."""
    try:
        lang = locale.getdefaultlocale()[0]
        if lang and lang.startswith("it"):
            return "it"
    except:
        pass
    return "en"


def get_language() -> str:
    """Get current language."""
    return _current_lang


def set_language(lang: str):
    """Set current language ('en' or 'it')."""
    global _current_lang
    if lang in TRANSLATIONS:
        _current_lang = lang


def init_language(db=None):
    """Initialize language from database or system."""
    global _current_lang
    if db:
        saved = db.get_setting("language")
        if saved in TRANSLATIONS:
            _current_lang = saved
            return
    _current_lang = get_system_language()


def tr(key: str) -> str:
    """Translate a string to current language."""
    translations = TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"])
    return translations.get(key, key)


def get_translated_subjects() -> list:
    """Get preset subjects translated to current language."""
    return [tr(s) for s in PRESET_SUBJECTS]
