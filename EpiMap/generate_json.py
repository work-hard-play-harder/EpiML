import os
import json
import decimal
import pandas as pd

from EpiMap.datasets import MiRNA2Disease


def load_results(filename):
    df = pd.read_csv(filename, header=0, sep='\t')
    return df


def scitific_notation(df, skip_col):
    new_df = []
    for index, row in df.iterrows():
        row = list(row)
        last_col = ['%.4E' % decimal.Decimal(x) for x in row[skip_col:]]
        new_row = row[:skip_col] + last_col
        new_df.append(new_row)

    return new_df


def load_json(filename):
    with open(filename, 'r') as fin:
        json_data = json.load(fin)

    return json_data['nodes'], json_data['links'], json_data['legends']


class MiRNAJson(object):
    main_nodes = []
    epis_nodes = []
    target_nodes = []

    # for force-directed graph
    nodes_json = []
    nodes_group_domain = set()
    links_json = []
    legend_json = []

    # for Hierarchical Edge Bundling(HEB)
    HEB_json = []

    def __init__(self, job_dir):
        self.job_dir = job_dir
        main_results_filename = os.path.join(self.job_dir, 'EBEN.main_result.txt')
        epis_results_filename = os.path.join(self.job_dir, 'EBEN.epis_result.txt')

        self.main_results = load_results(main_results_filename)
        self.epis_results = load_results(epis_results_filename)
        self.miRNA_target = MiRNA2Disease().miRNA_target

    def generate_nodes_json(self):
        self.main_nodes = self.main_results['feature'].drop_duplicates()
        self.epis_nodes = pd.concat([self.epis_results['feature1'],
                                     self.epis_results['feature2']]).drop_duplicates()
        all_miRNA_nodes = pd.concat([self.main_nodes, self.epis_nodes]).drop_duplicates()

        self.nodes_json = []
        for node in all_miRNA_nodes:
            if node in self.main_nodes.values:
                self.nodes_json.append({'id': node,
                                        'shape': 'triangle',
                                        'size': 100,
                                        'fill': 'red',
                                        'group': 'Main effect',
                                        'label': node,
                                        'level': 1,
                                        'url': 'http://www.mirbase.org/cgi-bin/query.pl?terms=' + node + '&submit=Search'
                                        })
                self.nodes_group_domain.add('main_effect')

            elif node in self.epis_nodes.values:
                self.nodes_json.append({'id': node,
                                        'shape': 'triangle',
                                        'size': 100,
                                        'fill': 'blue',
                                        'group': 'Epistatic effect',
                                        'label': node,
                                        'level': 1,
                                        'url': 'http://www.mirbase.org/cgi-bin/query.pl?terms=' + node + '&submit=Search'
                                        })
                self.nodes_group_domain.add('epis_effect')

        # filter related target nodes with ignore case
        self.related_target = self.miRNA_target[
            self.miRNA_target['miRNA'].str.lower().isin(all_miRNA_nodes.str.lower())].drop_duplicates()
        self.target_nodes = self.related_target['Validated target'].drop_duplicates()
        for node in self.target_nodes.values:
            self.nodes_json.append({'id': node,
                                    'shape': 'circle',
                                    'size': 50,
                                    'fill': 'purple',
                                    'group': 'Target gene',
                                    'label': node,
                                    'level': 2,
                                    'url': 'http://watson.compbio.iupui.edu:8080/miR2Disease/searchTarget.jsp?SearchUnit=target&SearchText=' + node + '&checkbox2=Causal&checkbox2=Unspecified'
                                    })
            self.nodes_group_domain.add('target')
        return self.nodes_json

    def generate_links_json(self):
        self.links_json = []
        # add epis link
        epis_links = self.epis_results[['feature1', 'feature2']].drop_duplicates()
        link_id = 0
        for index, link in epis_links.iterrows():
            link_id = index
            self.links_json.append({'id': link_id,
                                    'source': link['feature1'],
                                    'target': link['feature2'],
                                    'strength': 0.3})

        # add target link
        target_links = self.related_target[['miRNA', 'Validated target']].drop_duplicates()
        link_id += 1
        for index, link in target_links.iterrows():
            self.links_json.append({'id': link_id + index,
                                    'source': link['miRNA'].lower(),
                                    'target': link['Validated target'],
                                    'strength': 0.5})

        return self.links_json

    def generate_legend_json(self):
        self.legend_json = []
        if 'main_effect' in self.nodes_group_domain:
            self.legend_json.append({
                "label": "Main effect",
                "shape": "triangle",
                "color": "red"
            })
        if 'epis_effect' in self.nodes_group_domain:
            self.legend_json.append({
                "label": "Epistatic effect",
                "shape": "triangle",
                "color": "green"
            })
        if 'target' in self.nodes_group_domain:
            self.legend_json.append({
                "label": "Target gene",
                "shape": "circle",
                "color": "blue"
            })

        return self.legend_json

    def write_forceDirect_json(self):
        filename = os.path.join(self.job_dir, 'nodes_links.json')
        json_data = {'nodes': self.nodes_json,
                     'links': self.links_json,
                     'legends': self.legend_json}
        with open(filename, 'w') as fout:
            json.dump(json_data, fout, indent=4)

    def generate_miR_HEB_json(self):
        self.HEB_json = []
        for f1 in self.epis_nodes.values:
            f2_list = self.epis_results[self.epis_results['feature1'] == f1]['feature2'].tolist()
            element = {'name': 'miRNA.epis.' + f1, 'size': len(f2_list),
                       'effects': ['miRNA.epis.' + x for x in f2_list]}

            self.HEB_json.append(element)

        return self.HEB_json


class SNPJson(object):
    main_nodes = []
    epis_nodes = []
    target_nodes = []

    nodes_json = []
    nodes_group_domain = set()
    links_json = []
    legend_json = []

    def __init__(self, job_dir):
        self.job_dir = job_dir
        main_results_filename = os.path.join(self.job_dir, 'EBEN.main_result.txt')
        epis_results_filename = os.path.join(self.job_dir, 'EBEN.epis_result.txt')

        self.main_results = load_results(main_results_filename)
        self.epis_results = load_results(epis_results_filename)
        self.miRNA_target = MiRNA2Disease().miRNA_target

    def generate_nodes_json(self):
        self.main_nodes = self.main_results['feature'].drop_duplicates()
        self.epis_nodes = pd.concat([self.epis_results['feature1'],
                                     self.epis_results['feature2']]).drop_duplicates()
        all_miRNA_nodes = pd.concat([self.main_nodes, self.epis_nodes]).drop_duplicates()

        self.nodes_json = []
        for node in all_miRNA_nodes:
            if node in self.main_nodes.values:
                self.nodes_json.append({'id': node,
                                        'shape': 'triangle',
                                        'size': 80,
                                        'fill': 'red',
                                        'group': 'main_effect',
                                        'label': node,
                                        'level': 1
                                        })
                self.nodes_group_domain.add('main_effect')

            elif node in self.epis_nodes.values:
                self.nodes_json.append({'id': node,
                                        'shape': 'triangle',
                                        'size': 80,
                                        'fill': 'blue',
                                        'group': 'epis_effect',
                                        'label': node,
                                        'level': 1})
                self.nodes_group_domain.add('epis_effect')

        # filter related target nodes with ignore case
        self.related_target = self.miRNA_target[
            self.miRNA_target['miRNA'].str.lower().isin(all_miRNA_nodes.str.lower())].drop_duplicates()
        self.target_nodes = self.related_target['Validated target'].drop_duplicates()
        for node in self.target_nodes.values:
            self.nodes_json.append({'id': node,
                                    'shape': 'circle',
                                    'size': 50,
                                    'fill': 'purple',
                                    'group': 'target',
                                    'label': node,
                                    'level': 2})
            self.nodes_group_domain.add('target')
        return self.nodes_json

    def generate_links_json(self):
        self.links_json = []
        # add epis link
        epis_links = self.epis_results[['feature1', 'feature2']].drop_duplicates()
        link_id = 0
        for index, link in epis_links.iterrows():
            link_id = index
            self.links_json.append({'id': link_id,
                                    'source': link['feature1'],
                                    'target': link['feature2'],
                                    'color': 'black',
                                    'strength': 0.3})

        # add target link
        target_links = self.related_target[['miRNA', 'Validated target']].drop_duplicates()

        link_id += 1
        for index, link in target_links.iterrows():
            self.links_json.append({'id': link_id + index,
                                    'source': link['miRNA'].lower(),
                                    'target': link['Validated target'],
                                    'color': 'green',
                                    'strength': 0.5})

        return self.links_json

    def generate_legend_json(self):
        self.legend_json = []
        if 'main_effect' in self.nodes_group_domain:
            self.legend_json.append({
                "label": "main_effect",
                "shape": "triangle",
                "color": "red"
            })
        if 'epis_effect' in self.nodes_group_domain:
            self.legend_json.append({
                "label": "epis_effect",
                "shape": "triangle",
                "color": "green"
            })
        if 'target' in self.nodes_group_domain:
            self.legend_json.append({
                "label": "target",
                "shape": "circle",
                "color": "blue"
            })

        return self.legend_json

    def write_json(self):
        filename = os.path.join(self.job_dir, 'nodes_links.json')
        json_data = {'nodes': self.nodes_json,
                     'links': self.links_json,
                     'legends': self.legend_json}
        with open(filename, 'w') as fout:
            json.dump(json_data, fout, indent=4)
