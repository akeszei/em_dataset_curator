#!/usr/bin/env python3

## 2019-04-24: Wrote script
## 2020-11-11: Adapt script to work with reworked GIF_dataset_curator.py program

"""
    The RELION Select job uses a simple backup_selection.star file to label micrographs as either
    selected ('1'), or not selected ('0'), in a line-by-line format corresponding to the list of
    micrographs as they appear in the input .STAR file.

    This script is designed to take in a list of micrographs names from a file in the form:
        'marked_imgs.txt':
            mic_name_0001
            mic_name_0013
            ...
    And based on the input .STAR file to the Select job return a 'backup_selection.star' file
    with micrographs corresponding to those in the list are set as not selected.
"""

#############################
###     DEFINITIONS
#############################

def usage():
    """ This script requires several input arguments to work correctly. Check they exist, otherwise print usage and exit.
    """
    if not len(sys.argv) == 3:
        print("=================================================================================================================")
        print(" Create a 'backup_selection.star' file for a Select job (with CtfFind 'micrographs_ctf.star' as the input) ")
        print(" from a given list of bad micrographs, where listed micrographs in the file are set as inactive.")
        print(" Copy the output 'backup_selection.star' file into the Select job directory and run the job to implement.")
        print("=================================================================================================================")
        print(" USAGE:")
        print("    $ marked_imgs_to_backup_selection.py  marked_imgs.txt  /path/to/micrographs_ctf.star")
        print("=================================================================================================================")
        sys.exit()
    else:
        return

def parse_select_job_input_file(file):
    """ INPUT
            file = micrographs_ctf.star file used as input to the Select job
        RETURNS
            ordered_list_of_micrographs = list of entries as they appear in the input file, e.g.: [ _rlnMicrographName1, _rlnMicrographName2, ... ]
    """

    print(" >>> PARSING %s" % file)
    print("========================")

    ## initialize the list that will hold the name of each micrograph in the .star file
    ordered_list_of_micrographs = []

    with open(file, 'r') as f :
        line_num = 0

        line_num_rlnMicrographName = -1 ## line corresponding to the header that gives the column number
        line_num_data_begins = -1 ## line corresponding to the first data entry to read

        FIRST_LINE = True ## flag to trigger when found the first line after the header that is not empty

        for line in f :
            line_num += 1

            if "_rlnMicrographName" in line:
                line_num_rlnMicrographName = line_num
                column_num_rlnMicrographName = int(line.split()[1].replace("#",""))
                print(" _rlnMicrographName column number = ", column_num_rlnMicrographName)

            ## find the line number for the first data entry
            if ( line_num > line_num_rlnMicrographName ) and ( line_num_rlnMicrographName > 0 ):
                if not is_first_char(line, "_") and FIRST_LINE:
                    line_num_data_begins = line_num
                    print(" First data entry after header is on line = ", line_num_data_begins)
                    print("     FIRST DATA ENTRY : %s ..." % line[:65])
                    FIRST_LINE = False ## consume the flag

            ## parse the order of the micrographs as they appear by name in the star file
            if not FIRST_LINE and ( line_num >= line_num_data_begins ):
                current_micrograph_name = find_star_info(line, column_num_rlnMicrographName) ## false if no name found
                if (current_micrograph_name): ## avoids empty lines being added
                    ordered_list_of_micrographs.append(current_micrograph_name)
                    # print("MICROGRAPH NAME ADDED TO LIST : ", current_micrograph_name)
        print(" %s micrographs detected in star file" % len(ordered_list_of_micrographs))

        return ordered_list_of_micrographs

def is_first_char(input_string, char):
    """ INPUT:
            input_string = string of any length, typically a line in a file being parsed
            char = string of the character we want to compare with to determine a match
        RETURN:
            True  ; if char == first character in input_string
            False ; if char != first character in input_string, or if input_string is empty
    """
    input_string = input_string.strip() # remove empty spaces around string

    if len(input_string) == 0 :
        return False
    if ( input_string[0] == char ):
        return True
    return False

def find_star_info(line, column):
    """ For a given .STAR file line entry, extract the data at the given column index.
        If the column does not exist (e.g. for a header line read in), return 'False'
    """
    # break an input line into a list data type for column-by-column indexing
    line_to_list = line.split()
    try:
        column_value = line_to_list[column-1]
        return column_value
    except:
        return False

def parse_mics_from_file(file):
    """ Load a list of micrograph names from a file

        RETURNS
            mic_list : list of strings, e.g. [ 'mic_name1', 'mic_name2', ... ]
    """

    print("========================")
    print(" >>> PARSING %s" % file)
    print("========================")

    ## initialize a fresh variable to hold the names of each micrograph
    mic_list = []
    with open(file,'r') as f :
        for line in f :
            line = line.strip()
            # remove empty lines
            if len(line) == 0 :
                pass
            # comment handling
            elif line[0] == "#":
                pass
            elif len(line) > 0 :
                if line not in mic_list:
                    mic_list.append(line)
    print(" %s micrographs found in list" % len(mic_list) )
    return mic_list

def write_backup_selection(ordered_list_of_micrographs, marked_micrographs_list):

    print("========================")
    print(" >>> WRITING NEW 'backup_selection.star'")
    print("========================")

    with open("backup_selection.star", 'w') as f :  # mode 'w' overwrites any existing file, if present
        ############
        ## HEADER
        ############
        f.write("\n")
        f.write("data_\n")
        f.write("\n")
        f.write("loop_\n")
        f.write("_rlnSelected #1\n")

        ############
        ## BODY
        ############
        counter = 0 ## iterator to keep track of the number of micrographs unselected by this function
        for mic in ordered_list_of_micrographs:
            mic_path_removed = os.path.basename(mic)
            mic_path_removed_no_extension = os.path.splitext(mic_path_removed)[0]
            if mic_path_removed_no_extension in marked_micrographs_list:
                ## if the micrograph name appears in the marked list, set its value to '0' (e.g. not selected)
                f.write("\t0\n")
                counter += 1
            else:
                ## if the micrograph is not in the marked list, set its value to '1' (E.g. selected)
                f.write("\t1\n")

        print(" %s micrographs of %s total were set as unselected" % (counter, len(ordered_list_of_micrographs)) )

#############################
###     RUN BLOCK
#############################

if __name__ == "__main__":
    import string
    import os
    import sys

    usage()

    # read bash arguments $1 and $2 as variables
    marked_img_file = sys.argv[1]
    select_job_input_file = sys.argv[2]

    print("... Running job")
    print("========================")

    ordered_micrographs = parse_select_job_input_file(select_job_input_file)

    micrographs_in_marked_img_file = parse_mics_from_file(marked_img_file)

    write_backup_selection(ordered_micrographs, micrographs_in_marked_img_file)

    print("========================")
    print("... job completed.")
