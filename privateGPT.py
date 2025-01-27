from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.embeddings import LlamaCppEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import GPT4All, LlamaCpp
import os

load_dotenv()

llama_embeddings_model = os.environ.get("LLAMA_EMBEDDINGS_MODEL")
persist_directory = os.environ.get('PERSIST_DIRECTORY')

model_type = os.environ.get('MODEL_TYPE')
model_path = os.environ.get('MODEL_PATH')
model_n_ctx = os.environ.get('MODEL_N_CTX')

from constants import CHROMA_SETTINGS

# Global variable for the QA system
qa_system = None

def initialize_qa_system():
    llama = LlamaCppEmbeddings(model_path=llama_embeddings_model, n_ctx=model_n_ctx)
    db = Chroma(persist_directory=persist_directory, embedding_function=llama, client_settings=CHROMA_SETTINGS)
    retriever = db.as_retriever()
    callbacks = [StreamingStdOutCallbackHandler()]

    match model_type:
        case "LlamaCpp":
            llm = LlamaCpp(model_path=model_path, n_ctx=model_n_ctx, callbacks=callbacks, verbose=False)
        case "GPT4All":
            llm = GPT4All(model=model_path, n_ctx=model_n_ctx, backend='gptj', callbacks=callbacks, verbose=False)
        case _default:
            print(f"Model {model_type} not supported!")
            exit

    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

    return qa

def main():
    global qa_system
    qa_system = initialize_qa_system()

    while True:
        query = input("\nEnter a query: ")
        if query == "exit":
            break

        answer, docs = answer_query(query)

        print("\n\n> Question:")
        print(query)
        print("\n> Answer:")
        print(answer)

        for document in docs:
            print("\n> " + document.metadata["source"] + ":")
            print(document.page_content)

def answer_query(query, update_callback=None):
    global qa_system
    if qa_system is None:
        qa_system = initialize_qa_system()

    res = qa_system(query)
    answer, docs = res['result'], res['source_documents']

    if update_callback:
        update_callback(answer)
    else:
        return answer, docs

if __name__ == "__main__":
    main()
