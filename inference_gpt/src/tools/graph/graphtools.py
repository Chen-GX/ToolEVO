import networkx as nx
import numpy as np
import pandas as pd
import pickle
import os

class graph_toolkits():
    # init
    def __init__(self, path):
        self.path = path

        with open('{}/data/external_corpus/dblp/paper_net.pkl'.format(self.path), 'rb') as f:
            self.paper_net = pickle.load(f)

        with open('{}/data/external_corpus/dblp/author_net.pkl'.format(self.path), 'rb') as f:
            self.author_net = pickle.load(f)
        
        with open("{}/data/external_corpus/dblp/title2id_dict.pkl".format(self.path), "rb") as f:
            self.title2id_dict = pickle.load(f)
        with open("{}/data/external_corpus/dblp/author2id_dict.pkl".format(self.path), "rb") as f:
            self.author2id_dict = pickle.load(f)
        with open("{}/data/external_corpus/dblp/id2title_dict.pkl".format(self.path), "rb") as f:
            self.id2title_dict = pickle.load(f)
        with open("{}/data/external_corpus/dblp/id2author_dict.pkl".format(self.path), "rb") as f:
            self.id2author_dict = pickle.load(f)
    
    def load_graph(self, graph_name):
        if graph_name.lower() == 'dblp':
            
            return "DBLP data is loaded, including two graphs: AuthorNet and PaperNet."
        else:
            return f"We don't have the graph data named {graph_name}"
    
    def check_neighbours(self, graph_name, node):
        # graph, node = argument.split(', ')
        if graph_name == 'PaperNet':
            graph = self.paper_net
            dictionary = self.title2id_dict
            inv_dict = self.id2title_dict
        elif graph_name == 'AuthorNet':
            graph = self.author_net
            dictionary = self.author2id_dict
            inv_dict = self.id2author_dict
        neighbour_list = []
        num = 0
        for neighbour in graph.neighbors(dictionary[node]):
            num += 1
            if neighbour in inv_dict.keys():
                neighbour_list.append((inv_dict[neighbour], f"weight: {graph[dictionary[node]][neighbour]['weight']}"))  # dictionary[node]
        # collect infos of in_degree and out_degree
        if graph_name == 'PaperNet':
            return f"In degree: {graph.in_degree(dictionary[node])}; Out degree: {graph.out_degree(dictionary[node])}; {num} neighbors: " + str(neighbour_list)
        elif graph_name == 'AuthorNet':
            # collect_papers_infos
            paper_name = []
            unique_paper_name = []
            for neighbour_id in graph.neighbors(dictionary[node]):
                for paper_id in graph[dictionary[node]][neighbour_id]["papers"]:
                    paper_name.append(self.id2title_dict[paper_id])
                    if self.id2title_dict[paper_id] not in unique_paper_name:
                        unique_paper_name.append(self.id2title_dict[paper_id])

                # graph[dictionary[node]][neighbour_id]]["weight"]
            return f"Degree: {graph.degree(dictionary[node])}; {num} neighbors: " + str(neighbour_list) + f"; Total {len(paper_name)} papers; Paper list: {', '.join(unique_paper_name)}"

    # check the attributes of the nodes
    def check_nodes(self, graph, node):
        # graph, node = argument.split(', ')
        if graph == 'PaperNet':
            graph = self.paper_net
            dictionary = self.title2id_dict
            inv_dict = self.id2title_dict
        elif graph == 'AuthorNet':
            graph = self.author_net
            dictionary = self.author2id_dict
            inv_dict = self.id2author_dict
        return str(graph.nodes[dictionary[node]]) + f"; Degree: {graph.degree[dictionary[node]]}"  # graph.degree[dictionary[node]]

    # check the attributes of the edges
    def check_edges(self, graph, node1, node2):
        # graph, node1, node2 = argument.split(', ')
        if graph == 'PaperNet':
            graph = self.paper_net
            dictionary = self.title2id_dict
            inv_dict = self.id2title_dict
            edge = graph.edges[dictionary[node1], dictionary[node2]]
            return str(edge)
        elif graph == 'AuthorNet':
            graph = self.author_net
            dictionary = self.author2id_dict
            inv_dict = self.id2title_dict
            edge = graph.edges[dictionary[node1], dictionary[node2]]
            for id in range(len(edge['papers'])):
                edge['papers'][id] = inv_dict[edge['papers'][id]]
            return str(edge)

if __name__ == '__main__':

    graph_toolkits = graph_toolkits("./data/ToolQA-D")
    logs = graph_toolkits.load_graph('dblp')
    print(graph_toolkits.check_neighbours("AuthorNet", "Viswam Nathan"))
