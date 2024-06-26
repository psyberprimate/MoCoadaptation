import coadapt
import experiment_configs

import os, sys, time
import hashlib
import json
import wandb
import csv
import numpy as np


# put path to folder of model here, seed, weight and model folder name, aka last three parts from path
# example -> set_seed/0.0_1.0/Thu_Dec__7_20:55:59_2023__0f1677df[0.0, 1.0]

#path_to_folder = '/home/oskar/Thesis/priori/Model_scalarized/results_with_rescaling/set_seed/0.7_0.3/Thu_Jan__4_19:47:45_2024__139ccee8[0.7, 0.3]_1' 
path_to_folder = '/home/oskar/Thesis/priori/Model_scalarized_batch/results_with_rescaling/set_seed/test/0.1_0.9/Tue_Jan__9_22:20:46_2024__e01606ba[0.1, 0.9]_3'


seed = path_to_folder[-1]
newline=''

experiment_config = experiment_configs.sac_pso_batch #MORL dictiornary need for batch or sim
weight_index = 5 # dummy value for creating the class, we dont update the network so the weight doesnt matter here
project_name = "test" #"coadapt-scaled-test"#"coadapt-testing-scaling-tests"
run_name = "test" #"0, 1, 5"#"1, 0, 7"


def find_checkpoint(path_to_directory):
    """ Find the checkpoint for the model

    Returns: returns the int value of the last checkpoint or None
    """    
    checkpoints = []
    for file in os.listdir(path_to_directory):    
        if file.endswith('.csv'):
            checkpoint = int(file.split('_')[-1][:-4])
            checkpoints.append(checkpoint)
    if checkpoints:
        return max(checkpoints)
    else:
        return None
    
    
def read_morphology(path, checkpoint) -> list:
    
    """ Returns a list of values read from cvs file per row
    
    Returns: a list containing csv file values
    """    
    rows = []
    for filename in os.listdir(path):
        if filename.endswith(checkpoint):
            filepath = os.path.join(path, filename)
            with open(filepath, newline=newline) as file:
                reader = csv.reader(file)
                for row in reader:
                    rows.append(row)
    return rows


if __name__ == "__main__": 

    save_returns = True # Turn to True IF you want to save episodic returns, Turn to False when saving states and actions to csv file

    #Use to get last model checkpoint
    last_model_checkpoint_num = find_checkpoint(path_to_folder)#-1 # checkpoint
    print(last_model_checkpoint_num)
    last_model_checkpoint = f'checkpoint_design_{last_model_checkpoint_num}.chk'
    print("path_to_folder:", path_to_folder)
    print("last_model_checkpoint_num:", last_model_checkpoint_num)
    last_model_checkpoint = os.path.join(path_to_folder, 'checkpoints', last_model_checkpoint) # Set model path for correct checkpoint
    
    print(f"Last model checkpoint: {last_model_checkpoint}")
    
    #Load morphology -> link lenghts
    morphology_number = str(last_model_checkpoint_num)  + ".csv"
    model_file = read_morphology(path_to_folder, morphology_number) # read model csv file as list
    #print(model_file)
    link_lengths = np.array(model_file[1], dtype=float) # index link lengths from the file
    print(f"Link lenghts: {link_lengths}")
    
    folder = experiment_config['data_folder'] #MORL
    rand_id = hashlib.md5(os.urandom(128)).hexdigest()[:8]
    model_name = path_to_folder.split('/')[-1:]
    model_name = str(model_name[0])
    file_str = './' + folder + '/' + '__' + rand_id + "_" + model_name + '_test_' + str(last_model_checkpoint_num) + "_" + str(seed)
    experiment_config['data_folder_experiment'] = file_str # MORL

    #Create directory when not using video recording
    if not os.path.exists(file_str):
      os.makedirs(file_str)

    #initiliaze the class
    coadapt_test = coadapt.Coadaptation(experiment_config, weight_index, project_name, run_name)
    #load the networks
    coadapt_test.load_networks(last_model_checkpoint)
    file_path = coadapt_test._config['data_folder_experiment'] #filepath
    n = 30 #iterations
    coadapt_test._env.set_new_design(link_lengths) # Set new link lenghts
    #csv file name
    if save_returns:
        file_name ='episodic_rewards_run_'
    else:
        file_name ='states_actions_run_'
    
    with open(
            os.path.join(file_path,
                #'episodic_rewards_run_{}.csv'.format(run_name)
                '{}{}.csv'.format(file_name, run_name)
                ), 'w') as fd:
        #simulate the model
        
        if save_returns:
            running_speed = []
            energy_saving = []
        else:
            states = []
            actions = []
        
        for i in range(n):
            cwriter = csv.writer(fd)
            coadapt_test.initialize_episode()
            coadapt_test.execute_policy()
            #append iteration results to lists
            if save_returns:
                running_speed.append(coadapt_test._data_reward_1[0])
                energy_saving.append(coadapt_test._data_reward_2[0])
            else:
                states.append(coadapt_test._states[0])
                actions.append(coadapt_test._actions[0])
            print(f"Iteration done: {i}, Progress: {round((i/n)*100)}%")
        #save results to csv file
        #Maybe too many if's here?
        if save_returns:
            cwriter.writerow(link_lengths)
            cwriter.writerow(running_speed)
            cwriter.writerow(energy_saving)
        else:
            states_transposed = list(map(list, zip(*states)))
            actions_transposed = list(map(list, zip(*actions)))
            cwriter.writerow(["States"])
            cwriter.writerows(states_transposed)
            cwriter.writerow(["Actions"])
            cwriter.writerows(actions_transposed)
    #wandb.finish() Needed for wandb tracking