import streamlit as st
import requests
from bs4 import BeautifulSoup

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

st.title('EtimoloxIAs')

word = st.text_input('Introduza uma palavra:')
language = st.selectbox('Escolha uma língua:', ['Spanish', 'Portuguese', 'Galician', 'Latin'])

if st.button('Pesquisar etimologia'):
    etymology = fetch_etymology(word, language)
    if etymology:
        st.write('Etimologia:', etymology)
    else:
        st.write('Etimologia não encontrada.')
