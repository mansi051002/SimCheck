import nltk
import streamlit as st
import time
import requests
import os
import re
import PyPDF2
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords


# Helper function to make the API call
def make_api_call(data):
    # Replace the URL with your API endpoint
    url = "http://localhost:8000/in"
    response = requests.post(url, json=data)
    return response.json()

# Helper function to extract text from PDF
def pdf_to_text(pdf_file):

  pdf_reader = PyPDF2.PdfFileReader(pdf_file)

  text = ''
  for page_num in range(pdf_reader.numPages):
      page = pdf_reader.getPage(page_num)
      text += page.extractText()

  # print(text)
  return text

def tokenize(text):
    """Tokenize the text

    Parameters
    ----------
    text: String
        The message to be tokenized

    Returns
    -------
    List
        List with the clean tokens
    """
    text = text.lower()
    text = re.sub("[^a-zA-Z0-9]", " ", text)
    tokens = word_tokenize(text)
    tokens = [w for w in tokens if w not in stopwords.words("english")]

    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()

    clean_tokens_list = []
    for tok in tokens:
        lemmatizer_tok = lemmatizer.lemmatize(tok).strip()
        clean_tok = stemmer.stem(lemmatizer_tok)
        clean_tokens_list.append(clean_tok)

    return clean_tokens_list

# Streamlit app
def main():
    st.title('Document similarity')

    uploaded_files = st.file_uploader("Choose a PDF file", accept_multiple_files=True)
    if uploaded_files:
        if len(uploaded_files) == 2:
            file_1 = uploaded_files[0]
            file_2 = uploaded_files[1]

            st.write("PDFs successfully uploaded.")

            if st.button("Submit"):
                start = time.time()
                print("Conversion started")
                text1 = pdf_to_text(file_1)
                tokenized_text1 = " ".join(tokenize(text1))

                text2 = pdf_to_text(file_2)
                tokenized_text2 = " ".join(tokenize(text2))
                et = time.time()
                print(et - start)
                print("Conversion ended")
                my_obj = {
                    "t1": text1,
                    "t2": text2
                }
                print("Request Sent")
                start = time.time()
                res = make_api_call(my_obj)
                et = time.time()
                print(et - start)
                print("Response recieved")
                st.write(res)
                # data = {
                #     "file_1_text": extract_text_from_pdf(file_1),
                #     "file_2_text": extract_text_from_pdf(file_2)
                # }
                # response = make_api_call(data)
                # st.write("API Response:")
                # st.write(response)
        else:
            st.error("Please upload exactly 2 PDF files.")

if __name__ == '__main__':
    main()