# -*- coding: utf-8 -*-
"""
@author: lcalv
******************************************************************************
***                             INIT_MALLET                                 ***
******************************************************************************
"""
##############################################################################
#                                IMPORTS                                     #
##############################################################################
from auxiliary_functions import cmd
from Topic import Topic
from Model import Model

import pandas as pd
import numpy as np
import gzip
import os
import pathlib
import configparser
from colorama import Fore


##############################################################################
#                              CONFIG FILE                                   #
##############################################################################
file = 'config_project.ini'
config = configparser.ConfigParser()
config.read(file)

##############################################################################
#                           OUTPUT DOCUMENTS                                 #
##############################################################################
source_path = config['files']['source_path']
model_mallet = config['mallet']['model_mallet']
submodel_mallet = config['mallet']['submodel_mallet']
submodel_file = config['mallet']['submodel_file']
topic_state = config['out-documents']['topic_state']
topic_keys = config['out-documents']['topic_keys']
doc_topics = config['out-documents']['doc_topics']
topic_word_weights = config['out-documents']['topic_word_weights']
model_ids = config['out-documents']['model_ids']

##############################################################################
#                            MALLET CONFIG                                   #
##############################################################################
optimize_interval = config['mallet']['optimize_interval']
mallet_path = config['mallet']['mallet_path']

##############################################################################
#                           TRAIN FUNCTIONS                                  #
##############################################################################
def create_mallet(route_to_source, route_to_model):
    """Creates the mallet file given a set of txt files.
    
    Parameters:
    ----------
    * route_to_source - Route to the path were the text files are located.
    * route_to_model -  Route to model's folder.
    """
    output_mallet = (pathlib.Path(route_to_model) / model_mallet).as_posix()
    command  = (mallet_path + " import-file --input " + source_path 
                                          + " --output " + output_mallet 
                                          + " --keep-sequence --remove-stopwords")
    print(command)
    cmd(command)
    print("")
    print(Fore.GREEN+'Mallet file "data-model.mallet" created.'+ Fore.WHITE)
    print("")
    return

def create_sub_mallet(route_to_submodel):
    """Creates the mallet file of all particular submodel.
       If the submodel given to create the mallet file has already been trained,
       it removes all the files regarding to that training, with the exception
       of the subnew_XX.txt file.
    
    Parameters:
    ----------
    * route_to_submodel - Route to submodels folder.
    """
    output_mallet =  pathlib.Path(route_to_submodel / submodel_mallet).as_posix()
    input_txt =  pathlib.Path(route_to_submodel / submodel_file).as_posix()
    command  = (mallet_path + " import-file --input " + input_txt 
                                          + " --output " + output_mallet 
                                          + " --keep-sequence --remove-stopwords")
    cmd(command)
    print("")
    print(Fore.GREEN+"Mallet file submodel.mallet in "+ input_txt + " created." + Fore.WHITE)
    print("")
    return
        
def train_a_model(route_to_source, route_to_model, model):
    """Trains the model with a specified number of topics and a
       predefined optimize-interval.
       It also creates the txt document "model_ids", which contains
       the chemical description of all the topics created during the training.
    
    Parameters:
    ----------
    * route_to_source - Route to the path were the text files are located.
    * route_to_model  - Route to model's folder.
    * model           - Model object.
    """
    
    # Create mallet file
    create_mallet(route_to_source, route_to_model)
    
    # Input and output files
    model_dir =  pathlib.Path(route_to_model)
    trainig_input = (model_dir / model_mallet).as_posix()
    topic_state_model = (model_dir / topic_state).as_posix()
    topic_keys_model = (model_dir / topic_keys).as_posix()
    doc_topics_model = (model_dir/  doc_topics).as_posix()
    topic_word_weights_model = (model_dir / topic_word_weights).as_posix()
    # Train the model
    command = (mallet_path + " train-topics --input " + trainig_input 
                                                              + " --num-topics " + str(model.num_topics)
                                                              + " --optimize-interval " + str(optimize_interval)
                                                              + " --output-state " + topic_state_model
                                                              + " --output-topic-keys " + topic_keys_model
                                                              + " --output-doc-topics " + doc_topics_model
                                                              + " --topic-word-weights-file " + topic_word_weights_model)
    cmd(command)
    
    # Create model's topics
    topics, dictionary, topic_keys_weight = Topic.create_topics(model.num_topics, topic_word_weights_model, topic_keys_model)
    # Define model
    model.set_after_trained_parameters(topics, dictionary, topic_keys_weight, doc_topics_model)
    
    # Create document "model_ids"
    topic_ids = []
    for i in np.arange(0,len(model.topics_models),1):
        topic_ids.append("* TOPIC " + str(model.topics_models[i].get_topics()) + " -> " + str(model.topics_models[i].get_description()))
        text_to_save = (model_dir / model_ids).as_posix()
        np.savetxt(text_to_save, topic_ids, fmt='%s', encoding='utf-8')
    return

def train_a_submodel(submodel_name, submodel_path, submodel):
    """Trains a specific submodel with a specified number of topics and a
       predefined optimize-interval.
       It also creates the txt document "model_ids", which contains
       the chemical description of all the topics created during the training. 
     
    Parameters:
    ----------
    * submodel_name      - Str name of the submodel that is going to be trained
    * submodel_path      - Path of the submodel that is going to be trained
    * submodel           - Model object of the submodel that is goin to be trained
    """
    
    folder_dir = pathlib.Path(submodel_path)
    
    # Create mallet file
    create_sub_mallet(folder_dir)
    
    # Input and output files
    training_input = (folder_dir / submodel_mallet).as_posix()
    topic_state_model = (folder_dir / topic_state).as_posix()
    topic_keys_model = (folder_dir / topic_keys).as_posix() 
    doc_topics_model = (folder_dir/  doc_topics).as_posix()
    topic_word_weights_model = (folder_dir / topic_word_weights).as_posix()

    # Train the submodel
    command = (mallet_path + " train-topics --input " + training_input 
                                                          + " --num-topics " + str(submodel.num_topics)
                                                          + " --optimize-interval " + str(optimize_interval)
                                                          + " --output-state " + topic_state_model
                                                          + " --output-topic-keys " + topic_keys_model
                                                          + " --output-doc-topics " + doc_topics_model
                                                          + " --topic-word-weights-file " + topic_word_weights_model)
    cmd(command)
    
    # Create the topics of the submodel
    sub_topics, sub_dictionary, sub_topic_keys_weight = Topic.create_topics(submodel.num_topics, topic_word_weights_model , topic_keys_model)
    # Creates the submodel
    submodel.set_after_trained_parameters(sub_topics, sub_dictionary, sub_topic_keys_weight, doc_topics_model)
   
    # Create document "model_ids"
    sub_topic_ids = []
    for i in np.arange(0,len(submodel.topics_models),1):
        sub_topic_ids.append("* TOPIC " + str(submodel.topics_models[i].get_topics()) + " -> " + str(submodel.topics_models[i].get_description()))
        text_to_save = (folder_dir / model_ids).as_posix()
        np.savetxt(text_to_save, sub_topic_ids, fmt='%s', encoding='utf-8')
    print("")
    print(Fore.GREEN + '"' + submodel_name + '"' + " was trained with " + str(submodel.num_topics) + " topics." + Fore.WHITE)
    print("")
    return

def create_submodels(topic_id_list, route, time, option, model_obj, thr):
    """Creates a txt file "subnew_topic_id.txt" for each of the submodels 
       specified by the user. It creates, for each of the submodels, a folder 
       "Submodel_topic_id", where topic_id is the model's topic whose words
       conform the words of the new txt file created for training the submodel.
     
    Parameters:
    ----------
    * topic_id_list      - List containg all the topic's ids from which
                           the submodels are going to be created.
    * route              - Route to the father model folder, in which the
                           folders for each of the submodels expanded from 
                           such a model are going to be located
    * time               - Time of the system 
    * option             - Hierarchical topic model method that is going to be
                           used for the generation of the submodels
                           -- v1 : HTM in which the input documents to the 
                                   submodels are generated from the words that 
                                   belong to an specific topic in the father 
                                   model
                           -- v2: HTM in which the input documents to the 
                                  submodels are the complete documents that 
                                  contain the topic in the father model until
                                  a certain threshold
    * model_obj          - Object of the father model
    
    Returns:
    -------
    * submodels_paths - List structure containig all the submodels'paths
    * submodels_names - List structure containig all the submodels'names
    """
    model_dir = pathlib.Path(route)
    topic_state_model = (model_dir / topic_state).as_posix()
    
    submodels_paths = []
    submodels_names = []
    
    # 0 = document's id
    # 1 = document's name
    # 3 
    # 4 = word 
    # 5 = topic to which the word belongs
        
    with gzip.open(topic_state_model) as fin:
        topic_state_df = pd.read_csv(fin, delim_whitespace=True,
                                     names=['docid', 'NA1', 'NA2', 'NA3', 'word', 'tpc'],
                                     header = None, skiprows=3)
    
    topic_state_df.word.replace('nan', np.nan, inplace=True)
    topic_state_df.fillna('nan_value', inplace=True)
    
    if option == "v1":
        for top_id in np.arange(0, len(topic_id_list),1):
            topic_state_df_tpc = topic_state_df[topic_state_df['tpc']==top_id]
            topic_to_corpus = topic_state_df_tpc.groupby('docid')['word'].apply(list).reset_index(name='new')
            
            text_name = submodel_file 
            submodel_name = 'SubmodelFromTopic_' + str(topic_id_list[top_id]) + time
            submodel_dir = pathlib.Path(route)
            if not(os.path.isdir((submodel_dir / submodel_name).as_posix())):
                os.makedirs((submodel_dir / submodel_name).as_posix())
            text_to_save = (submodel_dir / submodel_name / text_name ).as_posix()
            
            with open(text_to_save, 'w', encoding='utf-8') as fout:
                for el in topic_to_corpus.values.tolist():
                    print(el)
                    fout.write(str(el[0]) + ' 0 ' + ' '.join(el[1])+ '\n')
    
            submodels_paths.append((submodel_dir / submodel_name).as_posix())
            submodels_names.append(submodel_name)
            print(Fore.GREEN + '"' + text_name + '"'+ " in submodel " + '"' + submodel_name + '"' + " created." + Fore.WHITE)
            print("")
    else: #option is v2
        print("entra en v2")
        # Incluir documentos completos que tienen una representación por encima de un determinado umbral
        for top_id in np.arange(0, len(topic_id_list),1):
             thetas_list = model_obj.thetas
             n_doc = 0
             #thr = 0.8
             words_to_keep = []
             for doc_thetas in thetas_list:
                 if doc_thetas[top_id] > thr:
                   print(doc_thetas[top_id])
                   print("")
                   topic_state_df_doc = topic_state_df[topic_state_df['docid'] == n_doc]
                   print(topic_state_df_doc)
                   print("")
                   doc_to_corpus = topic_state_df_doc.groupby('docid')['word'].apply(list).reset_index(name='new')
                   print(doc_to_corpus)
                   print("")
                   words_to_keep.append(doc_to_corpus)
                 n_doc +=1
             print(len(words_to_keep))
             
             text_name = submodel_file 
             submodel_name = 'SubmodelFromTopic_' + str(topic_id_list[top_id]) + time
             submodel_dir = pathlib.Path(route)
             if not(os.path.isdir((submodel_dir / submodel_name).as_posix())):
                 os.makedirs((submodel_dir / submodel_name).as_posix())
             text_to_save = (submodel_dir / submodel_name / text_name ).as_posix()
            
             with open(text_to_save, 'w', encoding='utf-8') as fout:
                 for i in words_to_keep:
                     for el in i.values.tolist():
                         print(el)
                         fout.write(str(el[0]) + ' 0 ' + ' '.join(el[1])+ '\n')
    
             submodels_paths.append((submodel_dir / submodel_name).as_posix())
             submodels_names.append(submodel_name)
             print(Fore.GREEN + '"' + text_name + '"'+ " in submodel " + '"' + submodel_name + '"' + " created." + Fore.WHITE)
             print("")
    return submodels_paths, submodels_names