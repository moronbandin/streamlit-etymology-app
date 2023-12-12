import streamlit as st
import requests
import re
from bs4 import BeautifulSoup

def fetch_declension_from_online_latin_dictionary(word):
    url = f"https://www.online-latin-dictionary.com/latin-dictionary-flexion.php?parola={word}"
    response = requests.get(url)

    if response.status_code != 200:
        return "Error al acceder a la página"

    soup = BeautifulSoup(response.content, 'html.parser')
    declension_tables = soup.find_all('table', class_='tb')

    declensions = {"SINGULAR": {}, "PLURAL": {}}
    for table in declension_tables:
        rows = table.find_all('tr')
        gender_number = table.find_previous('div').get_text(strip=True)

        for row in rows[1:]:  # Excluye la fila del encabezado
            cells = row.find_all('td')
            if len(cells) == 2:
                case = cells[0].get_text(strip=True)
                form = ''.join([span.get_text() for span in cells[1].find_all('span')])

                if "SINGULAR" in gender_number:
                    declensions["SINGULAR"][case] = form
                elif "PLURAL" in gender_number:
                    declensions["PLURAL"][case] = form

    return declensions

def declensions_to_markdown(declensions, order):
    markdown_table = "| CASO | SINGULAR | PLURAL |\n"
    markdown_table += "|------|----------|--------|\n"

    for case in order:
        singular = declensions["SINGULAR"].get(case, "")
        plural = declensions["PLURAL"].get(case, "")
        markdown_table += f"| {case} | {singular} | {plural} |\n"

    return markdown_table

def fetch_word_grammar_and_infinitive(word):
    # URL para la palabra y su clasificación gramatical
    url_lemma = f"https://www.online-latin-dictionary.com/latin-english-dictionary.php?parola={word}"
    response_lemma = requests.get(url_lemma)

    lemma_text, grammar_text = "", ""

    if response_lemma.status_code == 200:
        soup_lemma = BeautifulSoup(response_lemma.content, 'html.parser')
        lemma_span = soup_lemma.find('span', class_='lemma')
        grammar_span = soup_lemma.find('span', class_='grammatica')

        lemma_text = lemma_span.get_text(strip=True) if lemma_span else "Palabra no encontrada"
        grammar_text = grammar_span.get_text(strip=True) if grammar_span else "Clasificación gramatical no encontrada"
    else:
        return "Error al acceder a la página", "", None

    # URL para el infinitivo presente del verbo
    url_infinitive = f"https://www.online-latin-dictionary.com/latin-dictionary-flexion.php?parola={word}"
    response_infinitive = requests.get(url_infinitive)

    infinitive_present = None

    if response_infinitive.status_code == 200:
        soup_infinitive = BeautifulSoup(response_infinitive.content, 'html.parser')
        infinitive_section = soup_infinitive.find('b', string='INFINITIVE')
        if infinitive_section:
            infinitive_present_row = infinitive_section.find_next('tr', bgcolor="#FFFFFF")
            if infinitive_present_row:
                infinitive_present = ''.join(span.get_text() for span in infinitive_present_row.find_all('span'))
                
    return lemma_text, grammar_text, infinitive_present


def fetch_etymology(word, language):
    url = f"https://en.wiktionary.org/wiki/{word}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscando el encabezado del idioma
        language_header = soup.find('span', {'id': language})
        if not language_header:
            return None

        # Buscando la etimología dentro del encabezado del idioma
        etymology_text = ''
        found_etymology = False
        for sibling in language_header.parent.find_next_siblings():
            if sibling.name == 'h2':  # Fin de la sección del idioma
                break
            if sibling.name == 'h3' and 'Etymology' in sibling.text:
                found_etymology = True
                continue  # Saltar el encabezado de etimología
            elif found_etymology and sibling.find('span', {'class': 'mw-editsection'}):
                break  # Detener en el segundo "[edit]"
            if found_etymology:
                etymology_text += sibling.get_text()

        return etymology_text.strip() if found_etymology else None

    else:
        return None

# Función para traducir la clasificación gramatical
def traducir_clasificacion(clasificacion):
    traducciones = {
        r"\btransitive and intransitive verb\b": "verbo (in)transitivo",                
        r"\btransitive verb\b": "verbo transitivo",
        r"\bintransitive verb\b": "verbo intransitivo",
        r"\bI conjugation\b": "1ª conjugação",
        r"\bII conjugation\b": "2ª conjugação",
        r"\bIII conjugation\b": "3ª conjugação",
        r"\bIV conjugation\b": "4ª conjugação",
        r"\bending\b": "en",
        r"\banomalous\b": "irregular"
    }
    for ingles, portugues in traducciones.items():
        clasificacion = re.sub(ingles, portugues, clasificacion)
    return clasificacion

def buscar_genitivo(declensions):
    return declensions["SINGULAR"].get("Gen.", "")

st.title('EtimologIAs')

word = st.text_input('Introduza a palavra:')
language = st.selectbox('Escolha a língua:', ['Spanish', 'Portuguese', 'Galician', 'Latin'])

col1, col2 = st.columns(2)

with col1:
    if st.button('Etimologia'):
        etymology = fetch_etymology(word, language)
        if etymology:
            st.write('Etimologia:', etymology)
        else:
            st.write('Etimologia não encontrada.')

with col2:
    if st.button('Electro latino'):
        declensions = fetch_declension_from_online_latin_dictionary(word)
        lemma, grammar, infinitive = fetch_word_grammar_and_infinitive(word)

        genitivo = buscar_genitivo(declensions)
        grammar_traducida = traducir_clasificacion(grammar) if grammar else ""

        # Determinar qué información mostrar (infinitivo o genitivo)
        if infinitive:
            info_adicional = infinitive
        elif genitivo:
            info_adicional = genitivo
        else:
            info_adicional = ""

        # Mostrar la información
        if lemma:
            st.markdown(f"## {lemma}, {info_adicional}\n\n- {grammar_traducida}")

        # Mostrar la tabla de declinaciones si existe
        if declensions and (declensions != "Error al acceder a la página"):
            markdown_table = declensions_to_markdown(declensions, order=["Nom.", "Voc.", "Acc.", "Gen.", "Dat.", "Abl."])
            if any(declensions["SINGULAR"].values()) or any(declensions["PLURAL"].values()):
                st.markdown(markdown_table, unsafe_allow_html=True)
            else:
                pass