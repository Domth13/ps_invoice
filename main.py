import streamlit as st
from docxtpl import DocxTemplate
import tempfile
import os
import locale
import pandas as pd
import requests

# Set the locale to German (Germany)
locale.setlocale(locale.LC_ALL, 'de_DE.utf8')

# Define a function to add items to the invoice list
def add_item(position, menge, einheit, beschreibung, einzelpreis):
    gesamtpreis = menge * einzelpreis
    return {
        'Position': position,
        'Menge': f"{menge:.2f}".replace(".", ","),
        'Einheit': einheit,
        'Beschreibung': beschreibung,
        'Einzelpreis': f"{einzelpreis:.2f}".replace(".", ","),
        'Gesamtpreis': f"{gesamtpreis:.2f}".replace(".", ","),
    }

# Define a function to delete an item from the invoice list
def delete_item(item):
    st.session_state.invoice_items.remove(item)
    # Reassign positions to remaining items
    for index, remaining_item in enumerate(st.session_state.invoice_items):
        remaining_item['Position'] = f"{index + 1:03}"

# Initialize an empty list to store invoice items in session state
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = []

# Initialize position_index to 1
if 'position_index' not in st.session_state:
    if st.session_state.invoice_items:
        st.session_state.position_index = int(st.session_state.invoice_items[-1]['Position']) + 1
    else:
        st.session_state.position_index = 1

# Streamlit app header
st.title("Rechnung erstellen")

if st.button("Neue Rechnung"):
    st.session_state.invoice_items = []
    st.session_state.position_index = 1
    invoice_number, invoice_date, invoice_subject, invoice_bv = "", None, "", ""
    customer_salutation, customer_name, customer_adress, customer_postcode = "", "", "", ""
    menge, einheit, beschreibung, einzelpreis = None, None, None, None

# Input fields for user data
st.header("Rechnungsinformationen")
invoice_number = st.text_input("Rechnungsnummer:")
invoice_date = st.date_input("Datum:")
invoice_subject = st.text_input("Betreff: ")
invoice_bv = st.text_input("BV")
customer_salutation = st.selectbox("Anrede:", ["Herr", "Frau", "Firma"])
customer_name = st.text_input("Name:")
customer_adress = st.text_input("Straße/ Hausnummer")
customer_postcode = st.text_input("Plz Ort")

st.header("Positionen")
menge = st.number_input("Menge:")
einheit = st.text_input("Einheit:")
beschreibung = st.text_area("Beschreibung:")
einzelpreis = st.number_input("Einzelpreis:")

if st.button("Position hinzufügen"):
    if menge is not None and einheit and beschreibung and einzelpreis is not None:
        if st.session_state.invoice_items:
            st.session_state.position_index = int(st.session_state.invoice_items[-1]['Position']) + 1
        else:
            st.session_state.position_index = 1
        position_str = str(st.session_state.position_index).zfill(3)
        item = add_item(position_str, menge, einheit, beschreibung, einzelpreis)
        st.session_state.invoice_items.append(item)
        st.session_state.position_index += 1
        menge, einheit, beschreibung, einzelpreis = None, None, None, None

# Button to generate the invoice document at the bottom
if st.button("Rechnung erstellen"):
    # Get the template URL from the environment variable INVOICE_TEMPLATE_PATH
    invoice_template_path = os.getenv('INVOICE_TEMPLATE_PATH')

    # Debugging: Print the invoice_template_path
    st.write("Invoice Template Path:", invoice_template_path)

    if invoice_template_path:
        # Download the template file
        response = requests.get(invoice_template_path)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        # Load the invoice template
        doc = DocxTemplate(temp_file_path)

        sum_items = sum(float(item['Gesamtpreis'].replace(",", ".")) for item in st.session_state.invoice_items)
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
            'invoice_items': st.session_state.invoice_items,
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

# Display the list of items on the invoice
st.header("Übersicht")
if st.session_state.invoice_items:
    sum_items = sum(float(item['Gesamtpreis'].replace(",", ".")) for item in st.session_state.invoice_items)
    tax = round(sum_items * 0.19, 2)
    total = round(sum_items + tax, 2)
    st.write("Gesamt:", f"{sum_items:.2f}".replace(".", ","), "€")
    st.write("MwSt:", f"{tax:.2f}".replace(".", ","), "€")
    st.write("Gesamtpreis:", f"{total:.2f}".replace(".", ","), "€")
    
    items_table = []
    columns = st.columns(5)  # Create three columns

    column_names = ['Position', 'Menge', 'Einheit', 'Beschreibung', 'Einzelpreis', 'Gesamtpreis']
        
    for item_index, item in enumerate(st.session_state.invoice_items):
        delete_button = columns[item_index % 5].button(f"Löschen: {item['Position']}", key=item['Position'])
        if delete_button:
            delete_item(item)
            st.experimental_rerun()
        else:
            items_table.append([item['Position'], item['Menge'], item['Einheit'], item['Beschreibung'], item['Einzelpreis'], item['Gesamtpreis']])

    df = pd.DataFrame(items_table, columns=column_names)
    st.dataframe(df, hide_index=True)
