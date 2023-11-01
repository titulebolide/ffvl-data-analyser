"""
Realizes a statistical study over the glide angles calculated before 
in order to extract for each wing the average glide angle
as well as the standard deviation
"""

import json
import pickle
import numpy as np
import argparse
import os
import utils

def post_process_analysis(flights):
    wings_to_flight = {}
    total_flights_to_analyse = 0
    print("Reindexing")
    for id,f in flights.items():
        if f is None:
            continue
        if not "wing" in f or not "glide_angles" in f or not "sampling" in f:
            continue
        wing_id = int(f["wing"])
        if wing_id in wings_to_flight:
            wings_to_flight[wing_id].append(id)
        else:
            wings_to_flight[wing_id] = [id]
        total_flights_to_analyse += 1

    wings_perf = {}
    print(f"Calculating average and standart deviation on {total_flights_to_analyse} flights")
    no_iter = 0
    for wing_id in wings_to_flight:
        wings_perf[wing_id] = {}
        sum_av = 0
        sum_sq = 0
        weight = 0
        nb_sample = 0
        for flight_id in wings_to_flight[wing_id]:
            f = flights[flight_id]
            ga = np.array(f['glide_angles'])
            sampling = f['sampling']
            sum_av += np.sum(ga)*sampling
            sum_sq += np.sum(ga**2)*sampling
            weight += sampling*len(ga)
            nb_sample += len(ga)
            if no_iter % 10000 == 0:
                print(f"{round(no_iter/total_flights_to_analyse*100,1)} %")
            no_iter += 1

        mean = sum_av/weight
        std_deviation = ((sum_sq/weight) - (mean)**2)**(1/2)
        confidence_95 = 2*std_deviation/nb_sample**(1/2) # https://fr.wikipedia.org/wiki/Intervalle_de_confiance#Estimation_d'une_moyenne
        wings_perf[wing_id]['mean'] = mean
        wings_perf[wing_id]['dev_hist'] = std_deviation
        wings_perf[wing_id]['confidence'] = confidence_95

    return wings_perf


def main(infile, outfile):
    print("Loading flight file")
    with open(infile, "r") as f:
        flights = json.load(f)

    wings_perf = post_process_analysis(flights)

    print("Saving results")
    with open(outfile, "wb") as f:
        pickle.dump(wings_perf, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("workdir", type=str, help="Work directory")
    args = parser.parse_args()

    workdir = os.path.abspath(args.workdir)
    infile = os.path.join(workdir, "flights_analysed.json")
    outfile = os.path.join(workdir, "flights_stats.dat")

    if not os.path.isfile(infile):
        print("The input file does not exits. Exiting.")
        exit(1)

    if os.path.exists(outfile):
        if not utils.yesno("This file already exists. Override?", default_yes=False):
            print("Exiting.")
            exit(0)

    if not os.path.isdir(os.path.dirname(outfile)):
        print(f"{os.path.dirname(outfile)} is not a valid directory. Exiting.")
        exit(1)

    main(infile, outfile)
