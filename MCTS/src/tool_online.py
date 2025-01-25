import os
import argparse
import jsonlines
import sentence_transformers


from tools.text.agenda_retriever import create_chroma_db_local as agenda_create_chroma_db_local
# from tools.text.agenda_retriever import insert_to_db as agenda_insert_to_db
from tools.text.scirex_retriever import create_chroma_db_local as scirex_create_chroma_db_local
# from tools.text.scirex_retriever import insert_to_db as scirex_insert_to_db
from tools.graph.graphtools import graph_toolkits

root_path = "YOUR ROOT PATH"


def sentence_embedding(model, texts):
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings


class ToolQA_OnLine(object):


    def __init__(self, args) -> None:
        self.args = args

        # init tool
        self.init_agenda_retriever(args)
        print("init agenda retrieve success")
        self.init_scirex_retriever(args)
        print("init scirex retrieve success")
        self.init_graph(args.path)
        print("init graph success")

    
    def init_graph(self, path):
        # print(graph_name)
        self.graph = graph_toolkits(path)

    def init_agenda_retriever(self, args, is_local=True):
        EMBED_MODEL_NAME = f"{root_path}/model_cache/all-mpnet-base-v2"
        CHROMA_PERSIST_DIRECTORY = f"{root_path}/ToolQA-D/data/chroma_db/agenda"
        CHROMA_COLLECTION_NAME = "all"
        CHROMA_SERVER_HOST = ""
        CHROMA_SERVER_HTTP_PORT = ""
        FILE_PATH = f"{root_path}/ToolQA-D/data/external_corpus/agenda/agenda_descriptions_merged.jsonl"
        cuda_idxes = [args.tool_device]
        number_of_processes = len(cuda_idxes)
        input_texts = []
        self.agenda_db = agenda_create_chroma_db_local(CHROMA_PERSIST_DIRECTORY, CHROMA_COLLECTION_NAME)
        with open(FILE_PATH, 'r') as f:
            for item in jsonlines.Reader(f):
                input_texts.append(item["event"])
        print("Total Number of Agendas:", len(input_texts))
        # input_texts = np.array_split(input_texts, number_of_processes)

        # args = ((input_texts[i], EMBED_MODEL_NAME, cuda_idxes[i], is_local) for i in range(number_of_processes))

        # # if there is no file under the directory "/localscratch/yzhuang43/ra-llm/retrieval_benchmark/data/chroma_db/agenda", insert the data into the db
        # if len(os.listdir(CHROMA_PERSIST_DIRECTORY)) == 0:
        #     agenda_insert_to_db(input_texts, model_name=EMBED_MODEL_NAME, cuda_idx=cuda_idxes[0], db=self.agenda_db)

        # input_paths = np.array_split(input_texts, number_of_processes)
        # with ProcessPoolExecutor(number_of_processes) as executor:
        #     executor.map(agenda_insert_to_db, args)
        self.agenda_model = sentence_transformers.SentenceTransformer(EMBED_MODEL_NAME, device=f"cuda:{self.args.tool_device}")

        print("test agendas", self.agenda_retriever("What is the Jessica's genda on March 7th, 2023?"))

    def init_scirex_retriever(self, args, is_local=True):
        EMBED_MODEL_NAME = f"{root_path}/model_cache/all-mpnet-base-v2"
        CHROMA_PERSIST_DIRECTORY = f"{root_path}/ToolQA-D/data/chroma_db/scirex-v2"
        CHROMA_COLLECTION_NAME = "all"
        CHROMA_SERVER_HOST = ""
        CHROMA_SERVER_HTTP_PORT = ""
        FILE_PATH = f"{root_path}/ToolQA-D/data/external_corpus/scirex/Preprocessed_Scirex.jsonl"
        
        cuda_idxes = [args.tool_device]
        number_of_processes = len(cuda_idxes)
        input_texts = []
        # import pdb; pdb.set_trace()
        self.scirex_db = scirex_create_chroma_db_local(CHROMA_PERSIST_DIRECTORY, CHROMA_COLLECTION_NAME)
        with open(FILE_PATH, 'r') as f:
            for item in jsonlines.Reader(f):
                input_texts.append(item["content"])
        print("Total Number of papers:", len(input_texts))
        # input_texts = np.array_split(input_texts, number_of_processes)

        # args = ((input_texts[i], EMBED_MODEL_NAME, cuda_idxes[i], is_local) for i in range(number_of_processes))

        # # if there is no file under the directory "/localscratch/yzhuang43/ra-llm/retrieval_benchmark/data/chroma_db/agenda", insert the data into the db
        # if len(os.listdir(CHROMA_PERSIST_DIRECTORY)) == 0:
        #     scirex_insert_to_db(input_texts, model_name=EMBED_MODEL_NAME, cuda_idx=cuda_idxes[0], db=self.scirex_db)

        # input_paths = np.array_split(input_texts, number_of_processes)
        # with ProcessPoolExecutor(number_of_processes) as executor:
        #     executor.map(scirex_insert_to_db, args)
        self.scirex_model = sentence_transformers.SentenceTransformer(EMBED_MODEL_NAME, device=f"cuda:{self.args.tool_device}")

        print("test scirex", self.scirex_retriever("What is the corresponding EM score of the BiDAF__ensemble_ method on SQuAD1_1 dataset for Question_Answering task?"))

    def agenda_retriever(self, query):
        query_embedding = sentence_embedding(self.agenda_model, query).tolist()
        results = self.agenda_db.query(query_embeddings=query_embedding, n_results=3)
        retrieval_content = [result for result in results['documents'][0]]
        # print(retrieval_content)
        retrieval_content = '\n'.join(retrieval_content)
        return retrieval_content
    
    def scirex_retriever(self, query):
        query_embedding = sentence_embedding(self.scirex_model, query).tolist()
        results = self.scirex_db.query(query_embeddings=query_embedding, n_results=3)
        retrieval_content = [result for result in results['documents'][0]]
        # print(retrieval_content)
        retrieval_content = '\n'.join(retrieval_content)
        return retrieval_content
    


    def parse_and_perform_action(self, new_action_type:str, new_params: dict) -> str:
        # print(f"process:\n {new_action_type} \n {new_params}")
        scratchpad = ""

        if new_action_type == 'RetrieveAgenda':
            try:
                scratchpad += self.agenda_retriever(new_params['keyword']).strip('\n').strip()  # 返回3个最相关的文档(str)
            except:
                scratchpad += f'There is no information that can be matched in the database. Please try another query.'

        elif new_action_type == 'RetrieveScirex':
            try:
                scratchpad += self.scirex_retriever(new_params['keyword']).strip('\n').strip()
            except:
                scratchpad += f'There is no information that can be matched in the database. Please try another query.'

        elif new_action_type == 'LoadGraph':
            try:
                scratchpad += self.graph.load_graph(new_params['GraphName'])
            except:
                scratchpad += f'The graph you want to query in not in the list. Please change another graph for query.'

        elif new_action_type == 'NeighbourCheck':
            try:
                scratchpad += self.graph.check_neighbours(new_params['GraphName'], new_params['Node'])
            except:
                scratchpad += f'There is something wrong with the arguments you send for neighbour checking. Please modify it.'
        
        elif new_action_type == 'NodeCheck':
            try:
                scratchpad += self.graph.check_nodes(new_params['GraphName'], new_params['Node'])
            except KeyError:
                scratchpad += f'The node does not exist in the graph. Please modify it.'
            except:
                scratchpad += f'There is something wrong with the arguments you send for node checking. Please modify it.'
        
        elif new_action_type == 'EdgeCheck':
            try:
                scratchpad += self.graph.check_edges(new_params['GraphName'], new_params['Node1'], new_params['Node2'])
            except KeyError:
                scratchpad += f'There is no edge between the two nodes. Please modify it.'
            except:
                scratchpad += f'There is something wrong with the arguments you send for edge checking. Please modify it.'

        else:
            scratchpad += f"no such api {new_action_type}"

        return scratchpad

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device")
    args = parser.parse_args()

    gpu_device = os.environ.get('CUDA_VISIBLE_DEVICES', "0").split(',')
    # assert len(gpu_device) == 2
    args.device = 0
    args.tool_device = 0
    args.path = f"{root_path}/ToolQA-D"
    tool = ToolQA_OnLine(args)
    from tools.table.tabtools import table_toolkits
    table = table_toolkits()
