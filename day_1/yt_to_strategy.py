"""
This script shows how to create a strategy for a four-hour workday based on a YouTube video.
We're using an easy LangChain implementation to show how to use the different components of LangChain.
This is part of my '7 Days of LangChain' series. 

Check out the explanation about the code on my Twitter (@JorisTechTalk)

"""
"""
Docs: https://python.langchain.com/docs/use_cases/summarization

A central question for building a summarizer is how to pass your documents 
into the LLM's context window. Two common approaches for this are:

Stuff: Simply "stuff" all your documents into a single prompt. This is the 
simplest approach (see here for more on the StuffDocumentsChains, which is used for this method).

Map-reduce: Summarize each document on it's own in a "map" step and then 
"reduce" the summaries into a final summary (see here for more on the 
MapReduceDocumentsChain, which is used for this method).

Refine: The refine documents chain constructs a response by looping over the input 
documents and iteratively updating its answer. For each document, it passes all
 non-document inputs, the current document, and the latest intermediate answer 
 to an LLM chain to get a new answer.
This can be easily run with the chain_type="refine" specified.
"""

"""
TODO:
print number tokens
split by knowing number of tokens
Try return_intermediate_steps=True,
try map reduce
"""


import os

from langchain import LLMChain
from langchain.document_loaders import YoutubeLoader
from langchain.text_splitter import TokenTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.callbacks import get_openai_callback

verbose = False
outdir = 'day_1'

with get_openai_callback() as cb:

    # Set your OpenAI API Key.
    openai_api_key = os.getenv('OPENAI_KEY')

    # Load a youtube video and get the transcript
    url = "https://www.youtube.com/watch?v=aV4jKPFOjvk"
    loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
    data = loader.load()
    # data = [Document(page_content="when I was in college...'
    # , metadata={'source': 'aV4jKPFOjvk', 'title': 'The 4-Hour Workday (Focused Work Changed My Life)'
    # , 'description': 'Unknown', 'view_count': 186314
    # , 'thumbnail_url': 'https://i.ytimg.com/vi/aV4jKPFOjvk/hq720.jpg'
    # , 'publish_date': '2023-01-01 00:00:00', 'length': 1938, 'author': 'Dan Koe'})]
    print(data)
    num_chars = len(data[0].page_content)
    num_words = len(data[0].page_content.split(' '))
    print(f'#words={num_words} #chars={num_chars}')
    exit()
    # Split the transcript into shorter chunks.
    # First create the text splitter. The chunk_size is the maximum number of tokens in each chunk.
    # With the new gpt-3.5-turbo-16k model, you actually don't need it in this example, but it's good to know how to do it.
    text_splitter = TokenTextSplitter(chunk_size = 5000, chunk_overlap = 100)
    # text_splitter = <langchain.text_splitter.TokenTextSplitter object at 0x116819290>
    #print(text_splitter)

    # Then split the transcript into chunks.
    # The .split_documents() method returns the page_content attribute of the Document object.
    docs = text_splitter.split_documents(data)
    # docs = [Document(page_content="when I was ",metadata={'source': 'aV4jKPFOjvk', ...,
    #       , Document(page_content=" of them so",, metadata={'source': ... ]
    #print(docs)

    # The first prompt is for the initial summarization of a chunk. You can add any info about yourself or the topic you want.
    # You could specifically focus on a skill you have to get more relevant results.
    strategy_template = """
        You are an expert in creating strategies for getting a four-hour workday. You are a productivity coach and you have helped many people achieve a four-hour workday.
        You're goal is to create a detailed strategy for getting a four-hour workday.
        The strategy should be based on the following text:
        ------------
        {text}
        ------------
        Given the text, create a detailed strategy. The strategy is aimed to get a working plan on how to achieve a four-hour workday.
        The strategy should be as detailed as possible.
        STRATEGY:
    """

    PROMPT_STRATEGY = PromptTemplate(
        template=strategy_template, 
        input_variables=["text"]
    )

    # The second prompt is for the refinement of the summary, based on subsequent chunks.
    strategy_refine_template = (
    """
        You are an expert in creating strategies for getting a four-hour workday.
        You're goal is to create a detailed strategy for getting a four-hour workday.
        We have provided an existing strategy up to a certain point: {existing_answer}
        We have the opportunity to refine the strategy
        (only if needed) with some more context below.
        ------------
        {text}
        ------------
        Given the new context, refine the strategy.
        The strategy is aimed to get a working plan on how to achieve a four-hour workday.
        If the context isn't useful, return the original strategy.
    """
    )

    PROMPT_STRATEGY_REFINE = PromptTemplate(
        input_variables=["existing_answer", "text"],
        template=strategy_refine_template,
    )

    # Initialize the large language model. You can use the gpt-3.5-turbo-16k model or any model you prefer.
    # Play around with the temperature parameter to get different results. Higher temperature means more randomness. Lower temperature means more deterministic.
    llm = ChatOpenAI(openai_api_key=openai_api_key, model_name='gpt-3.5-turbo-16k', temperature=0.5)

    # Initiliaze the chain.
    # The verbose parameter prints the 'thought process' of the model. It's useful for debugging.
    strategy_chain = load_summarize_chain(llm=llm, chain_type='refine', verbose=verbose, question_prompt=PROMPT_STRATEGY, refine_prompt=PROMPT_STRATEGY_REFINE)
    strategy = strategy_chain.run(docs)
    print('Done with refine')

    # Now write the strategy to a file.
    with open(f'{outdir}/strategy.txt', 'w') as f:
        f.write(strategy)

    # Now use this strategy to create a plan.
    # The plan is a list of steps to take to achieve the goal.
    # The plan is based on the strategy.

    # Create the prompt for the plan.
    plan_template = """
        You are an expert in creating plans for getting a four-hour workday. You are a productivity coach and you have helped many people achieve a four-hour workday.
        You're goal is to create a detailed plan for getting a four-hour workday.
        The plan should be based on the following strategy:
        ------------
        {strategy}
        ------------
        Given the strategy, create a detailed plan. The plan is aimed to get a working plan on how to achieve a four-hour workday.
        Think step by step.
        The plan should be as detailed as possible.
        PLAN:
    """

    PROMPT_PLAN = PromptTemplate(template=plan_template, input_variables=["strategy"])

    # Initialize the chain.
    plan_chain = LLMChain(llm=llm, prompt=PROMPT_PLAN, verbose=verbose)
    plan = plan_chain(strategy)
    # plan = {'strategy': 'Original Strategy:\n1. Set a Clear Vision: Start by'...,
    #          'text': 'Step 1: Set a Clear Vision\n- Spend time...'}
    #print(plan)

    # Now write the plan to a file.
    with open(f'{outdir}/plan.txt', 'w') as f:
        f.write(plan['text'])

# Print the total cost of the API calls.
print(cb)
