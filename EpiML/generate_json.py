import os
import json
import decimal
import pandas as pd
import random
from EpiML.datasets import MiRNA2Disease


def load_results(filename):
    df = pd.read_csv(filename, header=0, sep='\t')
    return df


def scientific_notation(df, skip_col):
    new_df = []
    for index, row in df.iterrows():
        row = list(row)
        last_col = ['%.4E' % decimal.Decimal(x) for x in row[skip_col:]]
        new_row = row[:skip_col] + last_col
        new_df.append(new_row)

    return new_df


# def load_json(filename):
#     with open(filename, 'r') as fin:
#         json_data = json.load(fin)
#
#     return json_data['nodes'], json_data['links'], json_data['legends']


# class MiRNAJson(object):
#     main_nodes = []
#     epis_nodes = []
#     target_nodes = []
#
#     # for force-directed graph
#     nodes_json = []
#     nodes_group_domain = set()
#     links_json = []
#     legend_json = []
#
#     # for Hierarchical Edge Bundling(HEB)
#     HEB_json = []
#
#     def __init__(self, job_dir):
#         self.job_dir = job_dir
#         main_results_filename = os.path.join(self.job_dir, 'main_result.txt')
#         epis_results_filename = os.path.join(self.job_dir, 'epis_result.txt')
#
#         self.main_results = load_results(main_results_filename)
#         self.epis_results = load_results(epis_results_filename)
#         self.miRNA_target = MiRNA2Disease().miRNA_target
#
#     def generate_nodes_json(self):
#         self.main_nodes = self.main_results['feature'].drop_duplicates()
#         self.epis_nodes = pd.concat([self.epis_results['feature1'],
#                                      self.epis_results['feature2']]).drop_duplicates()
#         all_miRNA_nodes = pd.concat([self.main_nodes, self.epis_nodes]).drop_duplicates()
#
#         self.nodes_json = []
#         for node in all_miRNA_nodes:
#             if node in self.main_nodes.values:
#                 self.nodes_json.append({'id': node,
#                                         'shape': 'triangle',
#                                         'size': 100,
#                                         'group': 'Main effect',
#                                         'label': node,
#                                         'level': 1,
#                                         'url': 'http://www.mirbase.org/cgi-bin/query.pl?terms=' + node + '&submit=Search'
#                                         })
#                 self.nodes_group_domain.add('main_effect')
#
#             elif node in self.epis_nodes.values:
#                 self.nodes_json.append({'id': node,
#                                         'shape': 'triangle',
#                                         'size': 100,
#                                         'group': 'Epistatic effect',
#                                         'label': node,
#                                         'level': 1,
#                                         'url': 'http://www.mirbase.org/cgi-bin/query.pl?terms=' + node + '&submit=Search'
#                                         })
#                 self.nodes_group_domain.add('epis_effect')
#
#         # filter related target nodes with ignore case
#         self.related_target = self.miRNA_target[
#             self.miRNA_target['miRNA'].str.lower().isin(all_miRNA_nodes.str.lower())].drop_duplicates()
#         self.target_nodes = self.related_target['Validated target'].drop_duplicates()
#         for node in self.target_nodes.values:
#             self.nodes_json.append({'id': node,
#                                     'shape': 'circle',
#                                     'size': 50,
#                                     'group': 'Target gene',
#                                     'label': node,
#                                     'level': 2,
#                                     'url': 'http://watson.compbio.iupui.edu:8080/miR2Disease/searchTarget.jsp?SearchUnit=target&SearchText=' + node + '&checkbox2=Causal&checkbox2=Unspecified'
#                                     })
#             self.nodes_group_domain.add('target')
#         return self.nodes_json
#
#     def generate_links_json(self):
#         self.links_json = []
#         # add epis link
#         epis_links = self.epis_results.drop_duplicates()
#         link_id = 0
#         for index, link in epis_links.iterrows():
#             link_id = index
#             self.links_json.append({'id': link_id,
#                                     'source': link['feature1'],
#                                     'target': link['feature2'],
#                                     'strength': 0.3})
#
#         # add target link
#         target_links = self.related_target[['miRNA', 'Validated target']].drop_duplicates()
#         link_id += 1
#         for index, link in target_links.iterrows():
#             self.links_json.append({'id': link_id + index,
#                                     'source': link['miRNA'].lower(),
#                                     'target': link['Validated target'],
#                                     'strength': 0.5})
#
#         return self.links_json
#
#     def generate_legend_json(self):
#         self.legend_json = []
#         if 'main_effect' in self.nodes_group_domain:
#             self.legend_json.append({
#                 "label": "Main effect",
#                 "shape": "triangle",
#                 "color": "red"
#             })
#         if 'epis_effect' in self.nodes_group_domain:
#             self.legend_json.append({
#                 "label": "Epistatic effect",
#                 "shape": "triangle",
#                 "color": "green"
#             })
#         if 'target' in self.nodes_group_domain:
#             self.legend_json.append({
#                 "label": "Target gene",
#                 "shape": "circle",
#                 "color": "blue"
#             })
#
#         return self.legend_json
#
#     def write_forceDirect_nodes_links_json(self):
#         filename = os.path.join(self.job_dir, 'nodes_links.json')
#         json_data = {'nodes': self.nodes_json,
#                      'links': self.links_json}
#         with open(filename, 'w') as fout:
#             json.dump(json_data, fout, indent=4)
#
#     def write_forceDirect_legends_json(self):
#         filename = os.path.join(self.job_dir, 'legends.json')
#         json_data = {'legends': self.legend_json}
#         with open(filename, 'w') as fout:
#             json.dump(json_data, fout, indent=4)
#
#     def generate_miR_HEB_json(self):
#         self.HEB_json = []
#         for f1 in self.epis_nodes.values:
#             f2_list = self.epis_results[self.epis_results['feature1'] == f1]['feature2'].tolist()
#             element = {'name': 'epis.' + f1, 'size': len(f2_list),
#                        'effects': ['epis.' + x for x in f2_list]}
#
#             self.HEB_json.append(element)
#
#         return self.HEB_json
#
#     def write_am_graph_json(self):
#         am_graph_nodes_json = []
#         am_graph_links_json = []
#
#         for node in self.epis_nodes.values:
#             am_graph_nodes_json.append({'name': node,
#                                         'group': 'Epistatic effect',
#                                         'rank': random.randint(0, 100)
#                                         })
#
#         epis_nodes_list = self.epis_nodes.tolist()
#         epis_links = self.epis_results.drop_duplicates()
#         for index, link in epis_links.iterrows():
#             source_index = epis_nodes_list.index(link['feature1'])
#             target_index = epis_nodes_list.index(link['feature2'])
#             am_graph_links_json.append({'source': source_index,
#                                         'target': target_index,
#                                         'coff': link['coefficent value'],
#                                         # 'post': link['posterior variance'],
#                                         # 'tvalue': link['t-value'],
#                                         # 'pvalue': link['p-value'],
#                                         })
#
#         filename = os.path.join(self.job_dir, 'am_graph.json')
#         json_data = {'nodes': am_graph_nodes_json,
#                      'links': am_graph_links_json}
#         with open(filename, 'w') as fout:
#             json.dump(json_data, fout, indent=4)


class GenerateJson(object):
    main_nodes = []
    epis_nodes = []
    node_groups = set()

    UCSC_genomes_db = {'S. cerevisiae': 'sacCer3',
                       'C. elegans': 'ce11',
                       'Human': 'hg38',
                       'Mouse': 'mm10'}

    def __init__(self, job_dir, jobcategory):
        self.job_dir = job_dir
        self.species = jobcategory.split('(')[1][:-1]

        self.main_results = load_results(os.path.join(self.job_dir, 'main_result.txt'))
        self.main_nodes = self.main_results['feature'].drop_duplicates()
        if self.main_nodes.shape[0] > 0:
            self.node_groups.add('main_effect')

        self.epis_results = load_results(os.path.join(self.job_dir, 'epis_result.txt'))
        self.epis_nodes = pd.concat([self.epis_results['feature1'],
                                     self.epis_results['feature2']]).drop_duplicates()
        if self.epis_nodes.shape[0] > 0:
            self.node_groups.add('epis_effect')

        self.all_nodes = pd.concat([self.main_nodes, self.epis_nodes]).drop_duplicates()

    def generate_cn_graph_json(self):
        cn_graph_json = []
        for f1 in self.epis_nodes.values:
            f2_list = self.epis_results[self.epis_results['feature1'] == f1]['feature2'].tolist()
            element = {'name': 'epis.' + f1, 'size': len(f2_list),
                       'effects': ['epis.' + x for x in f2_list]}

            cn_graph_json.append(element)

        return cn_graph_json

    def generate_am_graph_json(self):

        am_graph_nodes_json = []
        am_graph_links_json = []

        for node in self.epis_nodes.values:
            am_graph_nodes_json.append({'name': node,
                                        'group': 'Epistatic effect',
                                        'rank': random.randint(0, 100)
                                        })

        epis_nodes_list = self.epis_nodes.tolist()
        epis_links = self.epis_results.drop_duplicates()
        for index, link in epis_links.iterrows():
            source_index = epis_nodes_list.index(link['feature1'])
            target_index = epis_nodes_list.index(link['feature2'])
            am_graph_links_json.append({'source': source_index,
                                        'target': target_index,
                                        'coff': link['coefficent'],
                                        # 'post': link['posterior variance'],
                                        # 'tvalue': link['t-value'],
                                        # 'pvalue': link['p-value'],
                                        })
        am_graph_json = {'nodes': am_graph_nodes_json,
                         'links': am_graph_links_json}

        return json.dumps(am_graph_json)

    def generate_gene_fd_graph_json(self):
        # for all nodes
        nodes_json = []
        for node in self.all_nodes:
            if node in self.main_nodes.values:
                feature_name = node.split('_')
                chr_name = feature_name[1]
                chr_position = int(feature_name[2])
                nodes_json.append({'id': node,
                                   'shape': 'triangle',
                                   'size': 80,
                                   'fill': 'red',
                                   'group': 'Main effect',
                                   'label': node,
                                   'level': 1,
                                   'type': 'gene',
                                   'url': 'https://genome.ucsc.edu/cgi-bin/hgTracks?db={0}&lastVirtModeType=default&lastVirtModeExtraState=&virtModeType=default&virtMode=0&nonVirtPosition=&position={1}%3A{2}%2D{3}&hgsid=696568993_Sf8X26qlPt8PnE4BDjm1qFYLxixM'.format(
                                       self.UCSC_genomes_db[self.species], chr_name, chr_position - 10,
                                                                                     chr_position + 10)
                                   })
            elif node in self.epis_nodes.values:
                feature_name = node.split('_')
                chr_name = feature_name[1]
                chr_position = int(feature_name[2])
                nodes_json.append({'id': node,
                                   'shape': 'triangle',
                                   'size': 80,
                                   'fill': 'blue',
                                   'group': 'Epistatic effect',
                                   'label': node,
                                   'level': 1,
                                   'type': 'gene',
                                   'url': 'https://genome.ucsc.edu/cgi-bin/hgTracks?db={0}&lastVirtModeType=default&lastVirtModeExtraState=&virtModeType=default&virtMode=0&nonVirtPosition=&position={1}%3A{2}%2D{3}&hgsid=696568993_Sf8X26qlPt8PnE4BDjm1qFYLxixM'.format(
                                       self.UCSC_genomes_db[self.species], chr_name, chr_position - 10,
                                                                                     chr_position + 10)
                                   })
        # for epis link
        links_json = []
        epis_links = self.epis_results[['feature1', 'feature2']].drop_duplicates()
        for index, link in epis_links.iterrows():
            links_json.append({'id': index,
                               'source': link['feature1'],
                               'target': link['feature2'],
                               'color': 'black',
                               'strength': 0.3})

        # for legends
        legend_json = []
        if 'main_effect' in self.node_groups:
            legend_json.append({
                "label": "Main effect",
                "shape": "triangle",
                "color": "red"
            })
        if 'epis_effect' in self.node_groups:
            legend_json.append({
                "label": "Epistatic effect",
                "shape": "triangle",
                "color": "green"
            })
        if 'target' in self.node_groups:
            legend_json.append({
                "label": "Target",
                "shape": "circle",
                "color": "blue"
            })

        # ensemble node, link and legends
        fd_graph_json = {'nodes': nodes_json, 'links': links_json, 'legends': legend_json}

        return json.dumps(fd_graph_json)

    def generate_microRNA_fd_graph_json(self):
        # for all nodes
        nodes_json = []
        for node in self.all_nodes:
            if node in self.main_nodes.values:
                nodes_json.append({'id': node,
                                   'shape': 'triangle',
                                   'size': 80,
                                   'fill': 'red',
                                   'group': 'Main effect',
                                   'label': node,
                                   'level': 1,
                                   'type': 'microRNA',
                                   'url': 'http://www.mirbase.org/cgi-bin/query.pl?terms={0}&submit=Search'.format(node)
                                   })
            elif node in self.epis_nodes.values:
                nodes_json.append({'id': node,
                                   'shape': 'triangle',
                                   'size': 80,
                                   'fill': 'blue',
                                   'group': 'Epistatic effect',
                                   'label': node,
                                   'level': 1,
                                   'type': 'microRNA',
                                   'url': 'http://www.mirbase.org/cgi-bin/query.pl?terms={0}&submit=Search'.format(node)
                                   })

        # for miRNA2Disease database
        miRNA_target = MiRNA2Disease().miRNA_target
        related_target = miRNA_target[
            miRNA_target['miRNA'].str.lower().isin(self.all_nodes.str.lower())].drop_duplicates()
        target_nodes = related_target['Validated target'].drop_duplicates()
        if target_nodes.shape[0] > 0:
            self.node_groups.add('target')
        for node in target_nodes.values:
            nodes_json.append({'id': node,
                               'shape': 'circle',
                               'size': 50,
                               'group': 'Target gene',
                               'label': node,
                               'level': 2,
                               'type': 'miRNA2Disease',
                               'url': 'http://watson.compbio.iupui.edu:8080/miR2Disease/searchTarget.jsp?SearchUnit=\
                                    target&SearchText={0}&checkbox2=Causal&checkbox2=Unspecified'.format(node)
                               })

        # for epis link
        links_json = []
        epis_links = self.epis_results[['feature1', 'feature2']].drop_duplicates()
        for index, link in epis_links.iterrows():
            links_json.append({'id': index,
                               'source': link['feature1'],
                               'target': link['feature2'],
                               'color': 'black',
                               'strength': 0.3})

        # for legends
        legend_json = []
        if 'main_effect' in self.node_groups:
            legend_json.append({
                "label": "Main effect",
                "shape": "triangle",
                "color": "red"
            })
        if 'epis_effect' in self.node_groups:
            legend_json.append({
                "label": "Epistatic effect",
                "shape": "triangle",
                "color": "green"
            })
        if 'target' in self.node_groups:
            legend_json.append({
                "label": "Target",
                "shape": "circle",
                "color": "blue"
            })

        # ensemble node, link and legends
        fd_graph_json = {'nodes': nodes_json, 'links': links_json, 'legends': legend_json}

        return json.dumps(fd_graph_json)

    def generate_other_fd_graph_json(self):
        # for all nodes
        nodes_json = []
        for node in self.all_nodes:
            if node in self.main_nodes.values:
                nodes_json.append({'id': node,
                                   'shape': 'triangle',
                                   'size': 80,
                                   'fill': 'red',
                                   'group': 'Main effect',
                                   'label': node,
                                   'level': 1,
                                   'type': 'other',
                                   'url': ''
                                   })
            elif node in self.epis_nodes.values:
                feature_name = node.split('_')
                chr_name = feature_name[1]
                chr_position = int(feature_name[2])
                nodes_json.append({'id': node,
                                   'shape': 'triangle',
                                   'size': 80,
                                   'fill': 'blue',
                                   'group': 'Epistatic effect',
                                   'label': node,
                                   'level': 1,
                                   'type': 'other',
                                   'url': ''
                                   })
        # for epis link
        links_json = []
        epis_links = self.epis_results[['feature1', 'feature2']].drop_duplicates()
        for index, link in epis_links.iterrows():
            links_json.append({'id': index,
                               'source': link['feature1'],
                               'target': link['feature2'],
                               'color': 'black',
                               'strength': 0.3})

        # for legends
        legend_json = []
        if 'main_effect' in self.node_groups:
            legend_json.append({
                "label": "Main effect",
                "shape": "triangle",
                "color": "red"
            })
        if 'epis_effect' in self.node_groups:
            legend_json.append({
                "label": "Epistatic effect",
                "shape": "triangle",
                "color": "green"
            })
        if 'target' in self.node_groups:
            legend_json.append({
                "label": "Target",
                "shape": "circle",
                "color": "blue"
            })

        # ensemble node, link and legends
        fd_graph_json = {'nodes': nodes_json, 'links': links_json, 'legends': legend_json}

        return json.dumps(fd_graph_json)

