# Obligation: when no chunk is relevant, the code declines without calling the model.
import rag_chatbot


# monkeypatch (built into pytest): swap a function for a fake during this test only
def test_declines_without_calling_the_model(monkeypatch):
    # fake retrieval: one chunk, farther than the cutoff below (no Ollama, no index needed)
    far = [{"text": "...", "source": "hr_policy.txt", "distance": 0.9}]
    monkeypatch.setattr(rag_chatbot, "retrieve_context", lambda question, n_results: far)

    # fake model: the test fails if the code calls it
    def no_model(*args):
        raise AssertionError("the model was called")
    monkeypatch.setattr(rag_chatbot, "chat", no_model)

    # answer() now gets the two fakes instead of the real functions
    reply, chunks = rag_chatbot.answer("Who approved the new parking policy?", threshold=0.5)

    # the fixed sentence, word for word, every time
    assert reply == rag_chatbot.DECLINE
