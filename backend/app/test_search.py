from embeddings import search

query = "What is the main idea of the document?"
results = search(query)
print("Top relevant chunks:")
for r in results:
    print(r)
    print("-----")
# backend/app/api.py