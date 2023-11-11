import streamlit as st
from docxtpl import DocxTemplate
import tempfile
import os
import locale
import pandas as pd
import requests

# Set the locale to German (Germany)
locale.setlocale(locale.LC_ALL, 'de_DE.utf8')

color_themes = ['#FFD700', '#FF6347', '#90EE90', '#ADD8E6', '#FFB6C1']

# Initialize session state variables for the input fields and their keys
if 'menge' not in st.session_state:
    st.session_state.menge = 0.00
if 'einheit' not in st.session_state:
    st.session_state.einheit = ""
if 'beschreibung' not in st.session_state:
    st.session_state.beschreibung = ""
if 'einzelpreis' not in st.session_state:
    st.session_state.einzelpreis = 0.00
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# Initialize session state variables for storing values
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = []

if 'last_moved' not in st.session_state:
    st.session_state.last_moved = None

# Function to clear input fields
def clear_input_fields():
    st.session_state.menge = 0.00
    st.session_state.einheit = ""
    st.session_state.beschreibung = ""
    st.session_state.einzelpreis = 0.00
    st.session_state.input_key += 1  # Increment key to reset fields

# Function to add items to the invoice list
def add_item(menge, einheit, beschreibung, einzelpreis):
    gesamtpreis = round(menge * einzelpreis, 2)
    # Assign a color from the color themes based on current number of items
    color = color_themes[len(st.session_state.invoice_items) % len(color_themes)]
    return {
        'Position': f"{len(st.session_state.invoice_items) + 1:03}",
        'Menge': menge,
        'Einheit': einheit,
        'Beschreibung': beschreibung,
        'Einzelpreis': einzelpreis,
        'Gesamtpreis': gesamtpreis,
        'Color': color  # Store color with the item
    }


# Function to update positions
def update_positions():
    for i, item in enumerate(st.session_state.invoice_items):
        item['Position'] = f"{i + 1:03}"

# Function to move an item in the invoice list
def move_item(index, direction):
    if direction == "up" and index > 0:
        st.session_state.invoice_items[index], st.session_state.invoice_items[index - 1] = st.session_state.invoice_items[index - 1], st.session_state.invoice_items[index]
        st.session_state.last_moved = index - 1
    elif direction == "down" and index < len(st.session_state.invoice_items) - 1:
        st.session_state.invoice_items[index], st.session_state.invoice_items[index + 1] = st.session_state.invoice_items[index + 1], st.session_state.invoice_items[index]
        st.session_state.last_moved = index + 1
    update_positions()

# Streamlit app layout
st.title("Rechnung erstellen")

# New invoice button
if st.button("Neue Rechnung"):
    st.session_state.invoice_items = []
    st.session_state.last_moved = None
    clear_input_fields()

# Invoice information fields
st.header("Rechnungsinformationen")
invoice_number = st.text_input("Rechnungsnummer:")
invoice_date = st.date_input("Datum:")
invoice_subject = st.text_input("Betreff: ")
invoice_bv = st.text_input("BV")
customer_salutation = st.selectbox("Anrede:", ["Herr", "Frau", "Firma"])
customer_name = st.text_input("Name:")
customer_adress = st.text_input("Straße/ Hausnummer")
customer_postcode = st.text_input("Plz Ort")

# Position fields with values from session state and unique keys
st.header("Positionen")
menge = st.number_input("Menge:", value=float(st.session_state.menge), format="%.2f", key=f'menge_{st.session_state.input_key}')
einheit = st.text_input("Einheit:", value=st.session_state.einheit, key=f'einheit_{st.session_state.input_key}')
beschreibung = st.text_area("Beschreibung:", value=st.session_state.beschreibung, key=f'beschreibung_{st.session_state.input_key}')
einzelpreis = st.number_input("Einzelpreis:", value=float(st.session_state.einzelpreis), format="%.2f", key=f'einzelpreis_{st.session_state.input_key}')

# Add position button
if st.button("Position hinzufügen"):
    if menge and einheit and beschreibung and einzelpreis:
        item = add_item(menge, einheit, beschreibung, einzelpreis)
        st.session_state.invoice_items.append(item)
        clear_input_fields()
        st.experimental_rerun()
    else:
        st.error("Bitte zuerst alle Felder dieser Postion ausfüllen!")

st.header("Übersicht")
if st.session_state.invoice_items:
    sum_items = sum(item['Gesamtpreis'] for item in st.session_state.invoice_items)
    tax = round(sum_items * 0.19, 2)
    total = round(sum_items + tax, 2)
    st.write("Gesamt:", f"{sum_items:.2f}".replace(".", ","), "€")
    st.write("MwSt:", f"{tax:.2f}".replace(".", ","), "€")
    st.write("Gesamtpreis:", f"{total:.2f}".replace(".", ","), "€")

# Editable fields for each invoice item
for i, item in enumerate(st.session_state.invoice_items):
    is_expanded = st.session_state.last_moved == i
    with st.expander(f"Position {item['Position']}", expanded=is_expanded):
        st.markdown(f"<p3 style='background-color: {item['Color']}; color: {item['Color']} ;'>00;</p>", unsafe_allow_html=True)
        item['Menge'] = st.number_input(f"Menge {i+1}", value=item['Menge'])
        item['Einheit'] = st.text_input(f"Einheit {i+1}", value=item['Einheit'])
        item['Beschreibung'] = st.text_area(f"Beschreibung {i+1}", value=item['Beschreibung'])
        item['Einzelpreis'] = st.number_input(f"Einzelpreis {i+1}", value=item['Einzelpreis'])
        item['Gesamtpreis'] = item['Menge'] * item['Einzelpreis']
        st.write(f"Gesamtpreis: {item['Gesamtpreis']:.2f}€")
        
       # Using columns with adjusted widths for button alignment
        col1, col2, col3, col4, col5 = st.columns([1, 1.5, 0.5, 1.5, 1])
        with col1:
            delete = st.button("Löschen", key=f"delete_{i}")
        with col2:
            st.write("")  # Spacer
        with col3:
            move_up = st.button("↑", key=f"up_{i}")
        with col4:
            move_down = st.button("↓", key=f"down_{i}")
        with col5:
            st.write("")  # Spacer

        if move_up:
            move_item(i, "up")
            st.experimental_rerun()
        if move_down:
            move_item(i, "down")
            st.experimental_rerun()
        if delete:
            st.session_state.invoice_items.pop(i)
            update_positions()
            st.session_state.last_moved = None
            st.experimental_rerun()
            

# Invoice creation button
if st.button("Rechnung erstellen"):
    # Get the template URL from the environment variable INVOICE_TEMPLATE_PATH
    invoice_template_path = os.getenv('INVOICE_TEMPLATE_PATH')

    if invoice_template_path:
        # Download the template file
        response = requests.get(invoice_template_path)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        # Load the invoice template
        doc = DocxTemplate(temp_file_path)

        formatted_invoice_items = []
        for item in st.session_state.invoice_items:
            formatted_item = item.copy()
            formatted_item['Einzelpreis'] = f"{item['Einzelpreis']:.2f}".replace('.', ',')
            formatted_item['Gesamtpreis'] = f"{round(item['Gesamtpreis'], 2):.2f}".replace('.', ',')  # Round and format
            formatted_invoice_items.append(formatted_item)

       # Sum up 'Gesamtpreis' directly as they are already floats
        sum_items = sum(item['Gesamtpreis'] for item in st.session_state.invoice_items)

        tax = round(sum_items * 0.19, 2)
        total = round(sum_items + tax, 2)


        context = {
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'invoice_subject': invoice_subject,
            'invoice_bv': invoice_bv,
            'customer_salutation': customer_salutation,
            'customer_name': customer_name,
            'customer_adress': customer_adress,
            'customer_postcode': customer_postcode,
            'invoice_items': formatted_invoice_items,
            'sum_items': f"{sum_items:.2f}".replace(".", ","),
            'tax': f"{tax:.2f}".replace(".", ","),
            'total': f"{total:.2f}".replace(".", ","),
        }

        doc.render(context)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "generated_invoice.docx")
            doc.save(temp_file_path)
            st.success("Rechnung erfolgreich erstellt. Einfach herunterladen.")
            with open(temp_file_path, "rb") as f:
                st.download_button("Rechnung herunterladen", f.read(), file_name=f"rechnung_{invoice_number}_{invoice_date}.docx")

    else:
        st.error("Error: INVOICE_TEMPLATE_PATH environment variable not set.")
