from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from rag.settings import settings

prompt_template = """
You will be given a legal document in the form of a string.
Your task is to return the given document but split into semantically coherent, meaningful chunks.
Anchor the splitting around legal keywords, sections and subsections
Make sure that each chunks consist out of at least a couple of meaningful words, contains enough nouns and could be 
interpreted as a standalone piece of information. 
For example if a section A. is followed by a limited number of subsections (MAX 3): consider them as a single chunk. Otherwise
split them into separate chunks.
For example legal keywords like THE FOLLOWING IS SET FORTH, should belong to the chunk that follows it, as it cannot be 
interpreted as a standalone piece of information.
Return the chunks by separating them with a /chunk/ token.
 
Legal text to split:
{document}
"""

async def llm_based_legal_document_chunking(document: str) -> List[str]:
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["document"],
    )
    model = ChatOpenAI(api_key=settings.OPENAI_API_KEY,model="gpt-4o")
    chain = prompt | model
    chunk_result = await chain.ainvoke(
        {
            "document": document
        }
    )
    chunks = chunk_result.content.split("/chunk/")
    return chunks

