import csv
from colorsys import hls_to_rgb
import matplotlib.pyplot as plt
import numpy as np
import os
import plotly.graph_objects as go

### NEW VERSION ###

#path='/home/oskar/Thesis/priori/model_comparison_results_sim' # paths need to be correct
path='/home/oskar/Thesis/priori/model_comparison_results_batch'
newline=''

save_file_name = 'link_length_comparison_' + path.split('_')[-1] # for saving the file if needed 

def get_distinct_colors(n):

    # Use this to get distict colors or just use a color map, both work.
    colors = []

    for i in np.arange(0., 360., 360. / n):
        h = i / 360.
        l = (50 + np.random.rand() * 10) / 100.
        s = (90 + np.random.rand() * 10) / 100.
        colors.append(hls_to_rgb(h, l, s))

    return colors


def convert_key_to_tuple(key):
    #return a tuple of values based on which the keys are sorted
    key_values = key.split('_')
    key_values = [value for value in key_values if value] 
    return tuple(map(float, key_values))


def sort_dictionaries(path):
    """ sorts through files for a given folder
    
    Returns: returns dictionaries with files values
    """  
    #Set up dictionaries
    value_mean = {}
    value_std = {}
    link_lengths = {}
    for directoryname in os.listdir(path):
        directorypath = os.path.join(path, directoryname)
        #Set up dictionaries
        value_mean[directoryname] = {}
        value_std[directoryname] = {}
        link_lengths[directoryname] = {}
        if os.path.isdir(directorypath):
            for directoryname2 in os.listdir(directorypath):
                #Set new directory path
                directorypath2 = os.path.join(directorypath, directoryname2)
                directory_keyname = directoryname2.split('[')[-1:]
                directory_keyname = directory_keyname[0].replace("]", "_").replace(", ", "_")
                # Go through and save data to dictionaries
                if os.path.isdir(directorypath2):
                    total_run_spd_reward = np.array([]) #reset when in new directory
                    total_energy_cons_reward = np.array([]) 
                    for filename in os.listdir(directorypath2):
                        if filename.endswith(".csv"):
                            filepath = os.path.join(directorypath2, filename)
                            with open(filepath, newline=newline) as file:
                                reader = csv.reader(file)
                                rows = [] # list for read values
                                link_lenghts_ind = np.array([]) # only the last link length needs to be saved since they are the same between the test run with same model
                                for row in reader:
                                    rows.append(row)
                                link_lenghts_ind = np.append(link_lenghts_ind, np.array(rows[0], dtype=float))
                                total_run_spd_reward = np.append(total_run_spd_reward, np.array(rows[1], dtype=float))
                                total_energy_cons_reward = np.append(total_energy_cons_reward, np.array(rows[2], dtype=float))
                                #values to dict
                    value_mean[directoryname][directory_keyname] = {'running_speed_returns_mean':np.mean(total_run_spd_reward), 'energy_consumption_returns_mean':np.mean(total_energy_cons_reward)}
                    link_lengths[directoryname][directory_keyname] = link_lenghts_ind
                    value_std[directoryname][directory_keyname] = {'running_speed_returns_std': np.std(total_run_spd_reward) , 'energy_consumption_returns_std': np.std(total_energy_cons_reward)}
    return value_mean, value_std, link_lengths


def bar_plot():
    """ Bar plot
    """  
    _, ax = plt.subplots()
    bar_width = 0.3
    off_set = 0.15
    index = np.arange(len(reward_mean))


    bar1 = ax.bar(index - off_set, reward_mean[:, 0], bar_width, label='Running Speed')
    bar2 = ax.bar(index + off_set, reward_mean[:, 1], bar_width, label='Energy Consumption')

    ax.errorbar(index - off_set, [sorted_mean[key1][key2]['running_speed_returns_mean']
                                for key1 in sorted_mean.keys() for key2 in sorted_mean[key1].keys()],
            yerr=ci_running_speed, fmt='none', color='black', capsize=5)

    ax.errorbar(index + off_set, [sorted_mean[key1][key2]['energy_consumption_returns_mean']
                                for key1 in sorted_mean.keys() for key2 in sorted_mean[key1].keys()],
            yerr=ci_energy_consumption, fmt='none', color='black', capsize=5)

    ax.set_xlabel('Weights')
    ax.set_ylabel('Mean sums')
    ax.set_title('Mean episodic returns for each weight of Running Speed and Energy Consumption for Each Weight')
    ax.set_xticks(index)
    ax.set_xticklabels([key2 for key1 in sorted_mean.keys() for key2 in sorted_mean[key1].keys()], rotation=45, ha='right')
    ax.legend()

def scatter_plot():
    """ Scatter plot
    """  
    _, ax2 = plt.subplots(figsize=(7, 7))
    ax2.set_ylabel('Energy')
    ax2.set_xlabel('Speed')
    #ax2.set_title('Mean Episodic Returns for Running Speed and Energy Consumption for Each Weight')
    #ax2.set_aspect('equal')

    unique_weight_groups = sorted(set(sorted_mean.keys()), key=convert_key_to_tuple)
    
    #distinct_colors = get_distinct_colors(len(unique_weight_groups)) # works better to get colors more apart from each other
    #adjusted_color_dict = {weight_group: distinct_colors[i] for i, weight_group in enumerate(unique_weight_groups)}
    adjusted_color_dict = {weight_group: plt.get_cmap('plasma')(i / len(unique_weight_groups)) for i, weight_group in enumerate(unique_weight_groups)}
    legend_added = {} # keep track of added legends for weight groups

    #shapes of markers
    marker_shapes = [".", ",", "o", "v", "^", "<", ">", "p", "*", "h", "D", "8", "s", ""]
    alp_value = 0.8

    for index, (key1, key2) in enumerate([(key1, key2) for key1 in sorted_mean.keys() for key2 in sorted_mean[key1].keys()]):
        mask = [key_compare == key1 for key_compare in sorted_mean.keys()]
        weight_group = unique_weight_groups[np.where(mask)[0][0]]  # Find the index where the mask is True
        color = adjusted_color_dict[weight_group]
        if weight_group not in legend_added:
            shape = marker_shapes[len(legend_added) % len(marker_shapes)]
            sc = ax2.scatter(reward_mean[index, 0], reward_mean[index, 1], s=150, color=adjusted_color_dict[weight_group], marker=shape, alpha=alp_value, label=weight_group)   
            legend_added[weight_group] = True
        else:
            sc = ax2.scatter(reward_mean[index, 0], reward_mean[index, 1], s=150, color=adjusted_color_dict[weight_group], marker=shape, alpha=alp_value)

        ax2.errorbar(reward_mean[index, 0], reward_mean[index, 1],
                     xerr=ci_running_speed[index],
                     yerr=ci_energy_consumption[index],
                     fmt='_',
                     capsize=0,
                     color=color)
    ###Add or dont add annotations per model###    
    ###annote the point to scatter plot###
    # for index, txt in enumerate([key2 for key1 in sorted_mean.keys() for key2 in sorted_mean[key1].keys()]):
    #    ax2.annotate(txt, (reward_mean[index, 0], reward_mean[index, 1]), textcoords="offset points", xytext=(0, 10), ha='center')
    ax2.legend()
    
    
def link_length_plot(save_file : bool = False, save_dir = 'link_length_comparison_results'):
    """ link length plot
    Set to 'True' to save plots into html files or 'False' to not save
    """  
    weight_categories = list(sorted_link_lengths.keys())
    distinct_error_colors = list(plt.get_cmap('plasma')(i / len(weight_categories)) for i, _ in enumerate(weight_categories)) # viridis_r

    os.makedirs(save_dir, exist_ok=True)

    for j in range(link_lengths_array.shape[2]):
        figv = go.Figure()
        figm = go.Figure()
        index_link_length = np.arange(link_lengths_array.shape[0])
        index_weigths = np.arange(link_lengths_array.shape[0])
        for i, weight_category in enumerate(weight_categories):
            
            color = f'rgb({distinct_error_colors[i][0]*255},{distinct_error_colors[i][1]*255},{distinct_error_colors[i][2]*255})'
            
            # MEAN AND STANDARD DEVIATION
            figm.add_trace(go.Scatter(
                    x=[weight_categories[i]],#weight_categories, #+ group_offset,
                    y=[link_lengths_mean_array[i, j]],
                    mode='markers+lines',
                    name=f'Weight : {weight_category} ',
                    marker=dict(color=color),
                    error_y=dict(
                    type='data',
                    array=[ci_link_length[i, j]],
                    visible=True,
                    color=color)
                ))
            figm.update_layout(
                        yaxis=dict(title='Link lenght',tickvals=index_link_length),
                        xaxis=dict(title='weights', tickvals=index_weigths, ticktext=weight_categories),
                        title=f'Comparison of Mean Link Lengths for Link {j + 1}',
                        showlegend=True
            )
            
            # REGULAR VALUES
            for _, y_value in enumerate(link_lengths_array[i, :, j]):
                figv.add_trace(go.Scatter(
                    x=[weight_categories[i]],  # Use a list with a single value
                    y=[y_value],
                    mode='markers+lines',
                    name=f'Weight : {weight_category}',
                    marker=dict(color=color),
                    line=dict(color=color)
                ))
                
            figv.update_layout(
                        yaxis=dict(title='Link lenght',tickvals=index_link_length),
                        xaxis=dict(title='weights', tickvals=index_weigths, ticktext=weight_categories),
                        title=f'Comparison of Link Lengths for Link {j + 1}',
                        showlegend=True
            )
        if save_file: 
            #save as html for comparisons
            html_file_path_mean = os.path.join(save_dir, f'Link_length_{j + 1}_mean_values.html')
            figm.write_html(html_file_path_mean)
            print(f'Figure saved as {html_file_path_mean}')
            html_file_path_reg = os.path.join(save_dir, f'Link_length_{j + 1}_values.html')
            figv.write_html(html_file_path_reg)
            print(f'Figure saved as {html_file_path_reg}')
            #save the means as pdf
            pdf_file_path_mean = os.path.join(save_dir, f'Link_length_{j + 1}_mean_values_{save_file_name.split("_")[-1]}_.pdf')
            figm.write_image(pdf_file_path_mean, format='pdf')
            print(f'Figure saved as {pdf_file_path_mean}')
            #save the values as pdf
            pdf_file_path_values = os.path.join(save_dir, f'Link_length_{j + 1}_values_{save_file_name.split("_")[-1]}_.pdf')
            figv.write_image(pdf_file_path_values, format='pdf')
            print(f'Figure saved as {pdf_file_path_values}')
            
        #figm.show() # uncomment to see the plots 
        #figv.show() # uncomment to see the plots 


if __name__ == "__main__":
    
    sample_count = 5 # ADD how many samples you have...
    value_mean, value_std, link_lengths = sort_dictionaries(path)
    # Sort dictionaries based on keys
    sorted_mean = dict(sorted(value_mean.items(), key=lambda item: convert_key_to_tuple(item[0])))
    sorted_std = dict(sorted(value_std.items(), key=lambda item: convert_key_to_tuple(item[0])))
    sorted_link_lengths = dict(sorted(link_lengths.items(), key=lambda item: convert_key_to_tuple(item[0]))) #Sort link lenghts

    # Sort the inner dictionaries based on keys
    # mean values
    for key, inner_dict in sorted_mean.items():
        #print(inner_dict.items())
        sorted_mean[key] = dict(sorted(inner_dict.items(), key=lambda item: convert_key_to_tuple(item[0])))
    # sums
    for key, inner_dict in sorted_std.items():
        sorted_std[key] = dict(sorted(inner_dict.items(), key=lambda item: convert_key_to_tuple(item[0]))) 
    # link lengths
    for key, inner_dict in sorted_link_lengths.items():
        sorted_link_lengths[key] = dict(sorted(inner_dict.items(), key=lambda item: convert_key_to_tuple(item[0]))) 

    #Calculate values to arrays
    reward_mean = np.array([(sorted_mean[key1][key2]['running_speed_returns_mean'], 
                                sorted_mean[key1][key2]['energy_consumption_returns_mean']) for key1 in sorted_mean.keys() for key2 in sorted_mean[key1].keys()])

    reward_std = np.array([(sorted_std[key1][key2]['running_speed_returns_std'], 
                                sorted_std[key1][key2]['energy_consumption_returns_std']) for key1 in sorted_std.keys() for key2 in sorted_std[key1].keys()])

    link_lengths_array = np.array([[weights[key] for key in weights] for weights in sorted_link_lengths.values()])
    link_lengths_mean_array = np.array([np.mean(list(weights.values()), axis=0) for weights in sorted_link_lengths.values()])
    link_lengths_std_array = np.array([np.std(list(weights.values()), axis=0) for weights in sorted_link_lengths.values()])
    
    #Set condidence inverval
    confidency_interval = 1.96 #3.89 #1.96#2.5576 #1.96  # Give confidence interval
    ci_running_speed = confidency_interval * (np.array([reward_std[i][0] for i in range(len(reward_std))]) / np.sqrt(sample_count))  # sample size is 5 since we have 5 different test runs  #np.sqrt(len(reward_std)))
    ci_energy_consumption = confidency_interval * (np.array([reward_std[i][1] for i in range(len(reward_std))]) / np.sqrt(sample_count))
    
    #ci_link_length = confidency_interval * (np.array(link_lengths_std_array / np.sqrt()))
    sem_link_length = link_lengths_std_array / np.sqrt(5)
    ci_link_length = confidency_interval * sem_link_length
    
    bar_plot()
    scatter_plot()
    if save_file_name:
        link_length_plot(True, save_file_name)
    else:
        link_length_plot(False)
    plt.show(block=True)
