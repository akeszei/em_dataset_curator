#!/usr/bin/env python3

## 2021-07-27: Created by Alex Keszei. A reworking of my previous GIF_dataset_curator to use .JPG format (smaller size images vs. GIF)
## 2021-08-29: Updated project. Renamed to em_dataset_curator.

"""
    Run this script in a directory of .JPG images (created from motion corrected
    .MRC files) to curate your dataset. Optionally, will automatically load .STAR
    coordinates from files matching the name, taking any with *_CURATED.STAR above
    any other duplicates. Will automatically create a *_CURATED.STAR file if one
    is not present. Designed to curate datasets in two ways:
        (i) Manually inspecting images and marking those to remove.
                d = mark image (red box will appear over sides of image)
                Ctrl + S = save a 'marked_imgs.txt' file in working directory with a list of marked images
                            This file can then be used to remove micrographs (E.g. via Select job in relion)
        (ii) Manually inspecting autopicked coordinates.
                Left click = Select particle (remove selected particle if already selected)
                Middle click = Hide all particle/highlights to see unmarked image below
                Right click = Activate erase brush, hold & drag to erase on-the-fly
                Mouse scrollwheel = Increase/decrease eraser tool brush size
                Ctrl + S = save current image coordinates into a *_CURATED.STAR file.
                Moving from one image to another will automatically execute a save function call as well.
"""

##########################
### FUNCTION DEFINITIONS
##########################

from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
import os, string, sys
from PIL import Image, ImageTk

from tkinter import ttk

class Gui:
    def __init__(self, master):
        """ The initialization scheme provides the grid layout, global keybindings,
            and widgets that constitute the main GUI window
        """
        self.master = master
        master.title("EM dataset curator")

        ## Menu bar layout
        ## initialize the top menu bar
        menubar = Menu(self.master)
        self.master.config(menu=menubar)
        ## add items to the menu bar
        dropdown_file = Menu(menubar)
        menubar.add_cascade(label="File", menu=dropdown_file)
        dropdown_file.add_command(label="Open image", command=self.load_file)
        dropdown_file.add_command(label="Load marked filelist", command=self.load_marked_filelist)
        # dropdown_file.add_command(label="Import .box coordinates", command=self.load_boxfile_coords)
        dropdown_file.add_command(label="Print marked imgs (Ctrl+S)", command=self.write_marked)
        # dropdown_file.add_command(label="Convert .box to _manualpick.star", command=self.write_manpick_files)
        dropdown_file.add_command(label="Exit", command=self.quit)

        dropdown_functions = Menu(menubar)
        menubar.add_cascade(label="Functions", menu=dropdown_functions)
        dropdown_functions.add_command(label="Auto-contrast", command=self.auto_contrast)
        dropdown_functions.add_command(label="Contrast from selection", command=self.contrast_by_selected_particles)
        dropdown_functions.add_command(label="Blur", command=self.gaussian_blur)

        ## Widgets
        self.canvas = Canvas(master, width = 650, height = 600, background="gray", cursor="cross red red")
        # self.current_dir = Label(master, font=("Helvetica", 12), text="")
        self.input_text = Entry(master, width=30, font=("Helvetica", 16), highlightcolor="blue", borderwidth=None, relief=FLAT, foreground="black", background="light gray")
        # self.browse = Button(master, text="Browse", command=self.load_file, width=10)
        self.settings_header = Label(master, font=("Helvetica, 16"), text="Settings")
        self.mrc_dimensions_label = Label(master, font=("Helvetica", 12), text=".MRC dimensions (X, Y)")
        self.input_mrc_dimensions = Entry(master, width=18, font=("Helvetica", 12))
        self.input_mrc_dimensions.insert(END, "%s, %s" % (mrc_pixel_size_x, mrc_pixel_size_y))
        self.mrc_box_size_label = Label(master, font=("Helvetica, 12"), text="Box size (Ang)")
        self.input_mrc_box_size = Entry(master, width=18, font=("Helvetica", 12))
        self.input_mrc_box_size.insert(END, "%s" % box_size)
        self.angpix_label = Label(master, font=("Helvetica", 12), text=".MRC Ang/pix")
        self.input_angpix = Entry(master, width=18, font=("Helvetica", 12))
        self.input_angpix.insert(END, "%s" % angpix)
        # self.box_size_ang_label = Label(master, font=("Helvetica", 11), text="Box size:")
        # self.box_size_ang = Label(master, font=("Helvetica italic", 10), text="%s Angstroms" % (box_size * angpix))
        self.img_size_label = Label(master, font=("Helvetica", 11), text="img dimensions (x,y) px:")
        self.img_size = Label(master, font=("Helvetica italic", 10), text="%s, %s" % (img_pixel_size_x, img_pixel_size_y))
        self.autopick_button = Button(master, text="Autopick", command=self.autopick, width=10)
        self.NEGATIVE_STAIN = BooleanVar(master, False)
        self.negative_stain_toggle = Checkbutton(master, text='Negative stain', variable=self.NEGATIVE_STAIN, onvalue=True, offvalue=False, command=self.toggle_negative_stain)
        self.input_autopick_min_distance = Entry(master, width=18, font=("Helvetica", 12))
        self.input_autopick_min_distance.insert(END, "%s" % autopick_min_distance)
        self.autopick_min_distance_label = Label(master, font=("Helvetica, 12"), text="Min. distance (Ang)")
        self.input_autopick_threshold = Entry(master, width=18, font=("Helvetica", 12))
        self.input_autopick_threshold.insert(END, "%s" % autopick_threshold)
        self.autopick_threshold_label = Label(master, font=("Helvetica, 12"), text="Threshold")
        self.input_autopick_blur = Entry(master, width=18, font=("Helvetica", 12))
        self.input_autopick_blur.insert(END, "%s" % autopick_blur)
        self.autopick_blur_label = Label(master, font=("Helvetica, 12"), text="Blurring factor")
        self.REFINE_METHOD = StringVar(master, "None")
        self.autopick_refine_method_label = Label(master, font=("Helvetica, 12"), text="Refinement method")
        self.input_autopick_refine_method = OptionMenu(master, self.REFINE_METHOD, "None", "Thresholding", "Contouring")
        self.SHOW_REFINEMENT_IMGS = BooleanVar(master, False)
        self.show_refinement_imgs_toggle = Checkbutton(master, text='Test refinement settings', variable=self.SHOW_REFINEMENT_IMGS, onvalue=True, offvalue=False)
        self.input_refinement_threshold = Entry(master, width=18, font=("Helvetica", 12))
        self.input_refinement_threshold.insert(END, "%s" % autopick_refine_threshold)
        self.refinement_threshold_label = Label(master, font=("Helvetica, 12"), text="Refinement threshold")
        self.separator = ttk.Separator(master, orient='horizontal')
        self.autopick_header = Label(master, font=("Helvetica, 16"), text="Autopicking")

        ## Widget layout
        self.input_text.grid(row=0, column=0, sticky=NW, padx=5, pady=5)
        self.canvas.grid(row=1, column=0, rowspan=100) #rowspan=0)
        # self.current_dir.grid(row=1, column=0, sticky=W, padx=5)

        self.settings_header.grid(row=1, column = 1, sticky = W)
        self.img_size_label.grid(row=2, column=1, padx=5, pady=0, sticky=S)
        self.img_size.grid(row=3, column=1, padx=5, pady=0, sticky=N)
        self.mrc_dimensions_label.grid(row=4, column=1, padx=5, sticky=(S, W))
        self.input_mrc_dimensions.grid(row=5, column=1, padx=5, pady=0, sticky=(N, W))
        self.mrc_box_size_label.grid(row=6, column=1, padx=5, pady=0, sticky=(S, W))
        self.input_mrc_box_size.grid(row=7, column=1, padx=5, pady=0, sticky=(N, W))
        self.angpix_label.grid(row=9, column=1, padx=5, pady=0, sticky=(S, W))
        self.input_angpix.grid(row=10, column=1, padx=5, pady=0, sticky=(N, W))
        # self.box_size_ang_label.grid(row=13, column=1, padx=5, pady=0, sticky=S)
        # self.box_size_ang.grid(row=14, column=1, padx=5, pady=0, sticky=N)
        # self.browse.grid(row=100, column=1, sticky=(S, E))

        self.separator.grid(row=20, column =1, sticky=EW)
        self.autopick_header.grid(row=21, column = 1, sticky = W)
        self.negative_stain_toggle.grid(row=22, column=1, padx=5, pady=0, sticky=N)
        self.autopick_min_distance_label.grid(row=23, column=1, padx=5, sticky=(S, W))
        self.input_autopick_min_distance.grid(row=24, column=1, padx=5, pady=0, sticky=(N, W))
        self.autopick_threshold_label.grid(row=25, column=1, padx=5, sticky=(S, W))
        self.input_autopick_threshold.grid(row=26, column=1, padx=5, pady=0, sticky=(N, W))
        self.autopick_blur_label.grid(row=27, column=1, padx=5, sticky=(S, W))
        self.input_autopick_blur.grid(row=28, column=1, padx=5, pady=0, sticky=(N, W))
        self.autopick_refine_method_label.grid(row=29, column=1, padx=5, pady=0, sticky=(N, W))
        self.input_autopick_refine_method.grid(row=30, column=1, padx =5, pady=0, sticky=N)
        self.refinement_threshold_label.grid(row=31, column=1, padx=5, sticky=(S, W))
        self.input_refinement_threshold.grid(row=32, column=1, padx=5, pady=0, sticky=(N, W))
        self.show_refinement_imgs_toggle.grid(row=33, column=1, padx=5, pady=0, sticky=N)
        self.autopick_button.grid(row=34, column=1, padx =5, pady=0, sticky=N)



        ## Key bindings
        self.canvas.bind('<Left>', lambda event: self.next_img('left'))
        self.canvas.bind('<Right>', lambda event: self.next_img('right'))
        self.canvas.bind('<z>', lambda event: self.next_img('left'))
        self.canvas.bind('<x>', lambda event: self.next_img('right'))
        self.canvas.bind('<d>', lambda event: self.mark_img())
        self.canvas.bind('<F1>', lambda event: self.debug())
        self.canvas.bind('<Escape>', lambda event: self.quit())
        self.input_text.bind('<Control-KeyRelease-a>', lambda event: self.select_all(self.input_text))
        self.input_text.bind('<Return>', lambda event: self.choose_img())
        self.input_text.bind('<KP_Enter>', lambda event: self.choose_img()) # numpad 'Return' key
        self.input_mrc_dimensions.bind('<Return>', lambda event: self.new_mrc_dimensions())
        self.input_mrc_dimensions.bind('<KP_Enter>', lambda event: self.new_mrc_dimensions()) # numpad 'Return' key
        self.input_mrc_box_size.bind('<Return>', lambda event: self.new_box_size())
        self.input_angpix.bind('<KP_Enter>', lambda event: self.new_angpix()) # numpad 'Return' key
        self.input_angpix.bind('<Return>', lambda event: self.new_angpix())
        self.input_mrc_box_size.bind('<KP_Enter>', lambda event: self.new_box_size()) # numpad 'Return' key
        self.input_autopick_min_distance.bind('<Return>', lambda event: self.refresh_autopick_variables())
        self.input_autopick_min_distance.bind('<KP_Enter>', lambda event: self.refresh_autopick_variables()) # numpad 'Return' key
        self.input_autopick_threshold.bind('<Return>', lambda event: self.refresh_autopick_variables())
        self.input_autopick_threshold.bind('<KP_Enter>', lambda event: self.refresh_autopick_variables()) # numpad 'Return' key
        self.input_autopick_blur.bind('<Return>', lambda event: self.refresh_autopick_variables())
        self.input_autopick_blur.bind('<KP_Enter>', lambda event: self.refresh_autopick_variables()) # numpad 'Return' key
        self.input_refinement_threshold.bind('<Return>', lambda event: self.refresh_autopick_variables())
        self.input_refinement_threshold.bind('<KP_Enter>', lambda event: self.refresh_autopick_variables()) # numpad 'Return' key
        self.canvas.bind('<Control-KeyRelease-s>', lambda event: self.write_marked())
        self.canvas.bind("<ButtonPress-1>", self.on_left_mouse_down)
        self.canvas.bind("<ButtonPress-2>", self.on_middle_mouse_press)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_mouse_release)

        self.canvas.bind("<ButtonPress-3>", self.on_right_mouse_press)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_mouse_release)
        self.canvas.bind("<Motion>", self.delete_brush_cursor)

        self.canvas.bind("<MouseWheel>", self.MouseWheelHandler) # Windows, Mac: Binding to <MouseWheel> is being used
        self.canvas.bind("<Button-4>", self.MouseWheelHandler) # Linux: Binding to <Button-4> and <Button-5> is being used
        self.canvas.bind("<Button-5>", self.MouseWheelHandler)

        self.master.protocol("WM_DELETE_WINDOW", self.quit)

        ## Run function to check for settings files and, if present load them into variables
        self.load_settings()

        ## Set focus to canvas, which has arrow key bindings
        self.canvas.focus_set()

    def refresh_autopick_variables(self):
        """ Update the global variables from user input in the main window
        """
        import re ## for use of re.findall() function to extract numbers from strings
        global autopick_min_distance, autopick_threshold, autopick_blur, autopick_refine_threshold

        user_input_min_distance = self.input_autopick_min_distance.get().strip()
        temp = re.findall(r'\d+', user_input_min_distance)
        res = list(map(int, temp))

        ## kill function if invalid entry is given
        if not len(res) == 1 or not isinstance(res[0], int) or not res[0] > 0:
            self.input_autopick_min_distance.delete(0,END)
            self.input_autopick_min_distance.insert(0, "min dist (ang)")
            return
        ## set the global box_size to the input field value
        autopick_min_distance = res[0]

        try:
            user_input_threshold = float(self.input_autopick_threshold.get().strip())
        except:
            self.input_autopick_threshold.delete(0,END)
            self.input_autopick_threshold.insert(0, "must be a float")
            return
        if 0 <= user_input_threshold <= 1:
            ## the value is in the correct range, so set the global to the input value
            autopick_threshold = user_input_threshold
        else:
            self.input_autopick_threshold.delete(0,END)
            self.input_autopick_threshold.insert(0, "must be in [0,1]")
            return

        try:
            user_input_blur = float(self.input_autopick_blur.get().strip())
        except:
            self.input_autopick_blur.delete(0,END)
            self.input_autopick_blur.insert(0, "must be a float")
            return
        if 0 <= user_input_blur:
            ## the value is in the correct range, so set the global to the input value
            autopick_blur = user_input_blur
        else:
            self.input_autopick_blur.delete(0,END)
            self.input_autopick_blur.insert(0, "must be in [0,inf]")
            return

        try:
            user_input_refine_threshold = float(self.input_refinement_threshold.get().strip())
        except:
            self.input_refinement_threshold.delete(0,END)
            self.input_refinement_threshold.insert(0, "must be a float")
            return
        if 0 <= user_input_refine_threshold < 1:
            ## the value is in the correct range, so set the global to the input value
            autopick_refine_threshold = user_input_refine_threshold
        else:
            self.input_refinement_threshold.delete(0,END)
            self.input_refinement_threshold.insert(0, "try in range [0,1)")
            return


        print("Updated autopick global variables :: autopick_min_distance = %s, autopick_threshold = %s, autopick_blur = %s, autopick_refine_threshold = %s" % (autopick_min_distance, autopick_threshold, autopick_blur, autopick_refine_threshold))

        ## revert focus to main canvas
        self.canvas.focus_set()
        return

    def toggle_negative_stain(self):
        if self.NEGATIVE_STAIN.get() == True:
            print("Negative stain mode is ON")
        else:
            print("Negative stain mode if OFF")
        return

    def autopick(self):
        global image_list, n, script_path, image_coordinates, angpix, autopick_min_distance, autopick_threshold, autopick_blur, autopick_refinement_method, autopick_refine_threshold

        try:
            sys.path.append(script_path)
            import peak_finder as peak_finder
        except :
            print("Abort autopick :: Check if peak_finder.py script is in same folder as this script and runs without error (i.e. can be compiled)!")
            return

        try:
            test_if_img_loaded = image_list[n]
        except:
            print("Abort autopick :: Image not loaded")
            return

        ## update globals in case they are not yet refreshed
        self.refresh_autopick_variables()
        self.new_angpix()
        self.new_box_size()

        angpix_gif = (mrc_pixel_size_x / img_pixel_size_x) * angpix
        print("MRC angpix = %s, GIF anpix = %s" % (angpix, angpix_gif))

        ## if we pass both exception statements, we have enough data to run the autopicker
        autopicked_gif_coordinates = peak_finder.get_peaks(image_list[n], int(box_size / angpix_gif), int(autopick_min_distance / angpix_gif), autopick_threshold, blur = autopick_blur, NEGATIVE_STAIN = self.NEGATIVE_STAIN.get(), REFINE = True, refine_method = self.REFINE_METHOD.get().lower(), refinement_threshold = autopick_refine_threshold, display_refinement_imgs = self.SHOW_REFINEMENT_IMGS.get(), PRINT_STAR = False)

        # reset the image_coordinates variable and repopulate it below
        image_coordinates = dict()

        ## pass the new coordinates into the appropriate data structure
        for coord in autopicked_gif_coordinates:
            image_coordinates[coord] = 'new_point'

        ## redraw data on screen
        self.load_img(n)

        return

    def debug(self):
        global image_coordinates, marked_imgs, img_box_size, box_size

        print("==========================")
        print("  DEBUG LOG: ")
        print("==========================")
        print("  img_box_size = ", img_box_size)
        print("  BOX_SIZE = ", box_size)
        print("  %s COORDINATES IN CURRENT IMG:" % len(image_coordinates))
        n = 0 # iterator variable
        for coord in image_coordinates:
            if (n == 3): print("        ..."); break
            print("        Key = ", coord, "   ==> calculated STAR coord: ", self.gif2star(coord), "   ==> recalculated GIF coord: ", self.star2gif(self.gif2star(coord)))
            print("      Value = ", image_coordinates[coord])
            n += 1 # advance the iterator
        print("==========================")
        print(" %s ENTRIES IN marked_imgs.txt:" % len(marked_imgs))
        n = 0 # iterator variable
        for entry in marked_imgs:
            if (n == 3): print("        ..."); break
            print("      %s" % marked_imgs[n])
            n += 1 # advance the iterator
        print("==========================")

    def quit(self):
        print("==============================================")
        print(" CLOSING PROGRAM")
        print("==============================================")
        ## get errors if I use this program to simply view a directory... only write out with Ctrl+S
        ## write out a settings file before closing
        self.save_settings()
        ## write out the list of marked files before closing
        # self.write_marked()
        ## write out the command necessary to rename the _CURATED.star file into _manpick.star file to ease-of-use (a typical next step after curation)
        # print("==============================================")
        # print(" >>> GUI_dataset_curator closed")
        print()
        print(" Convert curated star files into manualpick file names with the following bash command:")
        print()
        print('         for fname in *.star; do mv -v $fname ${fname/_CURATED.star/}_manualpick.star; done')
        print()
        ## close the program
        sys.exit()

    def gif2star(self, gif_coord):
        """ Remap a coordinate in gif-space into star-space (e.g. rescale the image back to full size and invert the y-axis)
                gif_coord = tuple, (x, y)
        """
        global img_pixel_size_x, mrc_pixel_size_x, mrc_pixel_size_y

        scale_factor = mrc_pixel_size_x / img_pixel_size_x # later I should make this an input parameter to avoid unccessary recalculation

        ### interpolate .MRC coordinate from .GIF position based on the scale factor
        rescaled_gif_coordinate_x = int(gif_coord[0] * scale_factor)
        rescaled_gif_coordinate_y = int(gif_coord[1] * scale_factor)

        ### invert y-axis to match RELION image coordinate convention
        ## 2021-09-10: WRONG implementation, RELION v.3.1 no longer inverts y-axis on .STAR data?
        # inverted_rescaled_gif_coordinate_y = mrc_pixel_size_y - rescaled_gif_coordinate_y
        inverted_rescaled_gif_coordinate_y = rescaled_gif_coordinate_y

        return (rescaled_gif_coordinate_x, inverted_rescaled_gif_coordinate_y)

    def star2gif(self, star_coord):
        """ Remap a coordinate in star-space into gif-space
                star_coord = tuple, (x, y)
        """
        global img_pixel_size_x, img_pixel_size_y, mrc_pixel_size_x, mrc_pixel_size_y

        ### invert y-axis to match GIF image coordinate conventions
        ## 2021-09-10: WRONG implementation, RELION v.3.1 no longer inverts y-axis on .STAR data?
        # inverted_star_coord = ( star_coord[0], mrc_pixel_size_y - star_coord[1] )
        inverted_star_coord = ( star_coord[0], star_coord[1] )

        scale_factor_x = img_pixel_size_x / mrc_pixel_size_x # later I should make this an input parameter to avoid unccessary recalculation
        scale_factor_y = img_pixel_size_y / mrc_pixel_size_y

        ### interpolate from .MRC to .GIF coordinates based on the scale factor
        rescaled_star_coordinate_x = int(inverted_star_coord[0] * scale_factor_x)
        rescaled_star_coordinate_y = int(inverted_star_coord[1] * scale_factor_y)

        return (rescaled_star_coordinate_x, rescaled_star_coordinate_y)

    def read_coords_from_star(self, starfile):
        """ Create a dictionary from data in a given .star file, mapping the coordinates to .gif coordinates of current image while keeping the original .star coordinate associated with the point
                starfile = string (file name to load)
            Dictionary created is of the form:
                image_coordinates = { (gif_x1, gif_y1) : (star_x1, star_y1), (gif_x2, gif_y2) : (star_x2, star_y2), ..., (gif_xn, gif_yn) : (star_xn, star_yn) }
        """
        global mrc_pixel_size_x, mrc_pixel_size_y, img_box_size, image_coordinates, box_size, img_pixel_size_x, img_pixel_size_y

        # reset the image_coordinates variable and repopulate it below
        image_coordinates = dict()

        header_size = self.header_length(starfile)
        star_X_coord_column = self.find_star_column(starfile, "_rlnCoordinateX", header_size)
        star_Y_coord_column = self.find_star_column(starfile, "_rlnCoordinateY", header_size)

        with open(starfile, 'r') as f:
            counter = 0
            for line in f:
                counter += 1

                ## avoid reading into the header
                if (counter <= header_size): continue

                star_X_coord = self.find_star_info(line, star_X_coord_column)
                star_Y_coord = self.find_star_info(line, star_Y_coord_column)

                ## avoid empty lines by checking if the X and Y coordinates exist
                if not star_X_coord:
                    continue
                if not star_Y_coord:
                    continue

                star_coord = (int(float(star_X_coord)), int(float(star_Y_coord)))
                gif_coord = self.star2gif(star_coord)

                image_coordinates[ gif_coord ] = star_coord # data are linked in this way to avoid transformation data loss
                # print("STAR coordinate found : " , star_coord, "  ==> calculated GIF coord: " , gif_coord)

            print(">> %s lines read from star file %s" % (counter, starfile) )
        return

    def update_input_widgets(self):
        global mrc_pixel_size_x, mrc_pixel_size_y, box_size, angpix, autopick_threshold, autopick_min_distance, autopick_blur, autopick_refine_threshold

        self.input_mrc_dimensions.delete(0,END)
        self.input_mrc_dimensions.insert(0, "%s, %s" % (mrc_pixel_size_x, mrc_pixel_size_y) )

        self.input_mrc_box_size.delete(0,END)
        self.input_mrc_box_size.insert(0, box_size)

        self.input_angpix.delete(0,END)
        self.input_angpix.insert(0, angpix)

        self.input_autopick_threshold.delete(0,END)
        self.input_autopick_threshold.insert(0, autopick_threshold)

        self.input_autopick_min_distance.delete(0,END)
        self.input_autopick_min_distance.insert(0, autopick_min_distance)

        self.input_autopick_blur.delete(0,END)
        self.input_autopick_blur.insert(0, autopick_blur)

        self.input_refinement_threshold.delete(0,END)
        self.input_refinement_threshold.insert(0, autopick_refine_threshold)

        # self.box_size_ang.config(text="%d Angstroms" % (box_size * angpix))
        return

    def save_settings(self):
        """ Write out a settings file for ease of use on re-launching the program in the same directory
        """
        global image_list, n, mrc_pixel_size_x, mrc_pixel_size_y, angpix, brush_size, box_size, autopick_min_distance, autopick_threshold, autopick_blur, autopick_refine_threshold
        current_img = image_list[n] # os.path.splitext(image_list[n])[0]
        ## save a settings file only if a project is actively open, as assessed by image_list being populated
        if len(image_list) > 0:
            with open('em_dataset_curator.config', 'w') as f :
                f.write("## Last used settings for em_dataset_curator.py\n")
                f.write("mrc_pixel_size_x %s\n" % mrc_pixel_size_x)
                f.write("mrc_pixel_size_y %s\n" % mrc_pixel_size_y)
                f.write("angpix %s\n" % angpix)
                f.write("brush_size %s\n" % brush_size)
                f.write("img_on_save %s\n" % current_img)
                f.write("box_size %s\n" % box_size)
                f.write("autopick_min_distance %s\n" % autopick_min_distance)
                f.write("autopick_threshold %s\n" % autopick_threshold)
                f.write("autopick_blur %s\n" % autopick_blur)
                f.write("autopick_refine_threshold %s\n" % autopick_refine_threshold)

        print(" >> Saved current settings to 'em_dataset_curator.config'")

    def load_settings(self):
        """ On loadup, search the directory for input files and load them into memory automatically
                >> marked_imgs.txt :: load these filenames into the 'marked_imgs' list variable
        """
        global box_size, image_list, n, image_coordinates, img_pixel_size_x, img_pixel_size_y, mrc_pixel_size_x, mrc_pixel_size_y, img_box_size, img_on_save, img_on_save, angpix, marked_imgs, autopick_min_distance, autopick_threshold, autopick_blur, autopick_refine_threshold

        ## reset marked_imgs global variable
        marked_imgs = []
        ## repopulate the global marked_imgs variable based on the file 'marked_imgs.txt', if present
        if os.path.exists('marked_imgs.txt'):
            ## update marked file list with file in directory
            with open('marked_imgs.txt', 'r') as f :
                for line in f:
                    if not line.strip() in marked_imgs:
                        marked_imgs.append(line.strip())

        settingsfile = 'em_dataset_curator.config'

        if os.path.exists(settingsfile):
            ## update marked file list with file in directory
            with open(settingsfile, 'r') as f :
                for line in f:
                    line2list = line.split()
                    if not '#' in line2list[0]: ## ignore comment lines
                        if line2list[0] == 'mrc_pixel_size_x':
                            mrc_pixel_size_x = int(line2list[1])
                        elif line2list[0] == 'mrc_pixel_size_y':
                            mrc_pixel_size_y = int(line2list[1])
                        elif line2list[0] == 'angpix':
                            angpix = float(line2list[1])
                        elif line2list[0] == 'brush_size':
                            brush_size = int(line2list[1])
                        elif line2list[0] == 'img_on_save':
                            img_on_save = line2list[1]
                        elif line2list[0] == 'box_size':
                            box_size = int(line2list[1])
                        elif line2list[0] == 'autopick_min_distance':
                            autopick_min_distance = int(line2list[1])
                        elif line2list[0] == 'autopick_threshold':
                            autopick_threshold = float(line2list[1])
                        elif line2list[0] == 'autopick_blur':
                            autopick_blur = float(line2list[1])
                        elif line2list[0] == 'autopick_refine_threshold':
                            autopick_refine_threshold = float(line2list[1])

            # print(mrc_pixel_size_x, mrc_pixel_size_y, angpix, brush_size, img_on_save)

            # extract file information from selection
            file_name = img_on_save #+ '.gif'
            print("File selected: "+ file_name)

            # erase any previous image list and repopulate it with the new directory
            image_list = []
            image_list = self.images_in_dir('.')

            # find the index of the selected image in the new list
            try:
                n = image_list.index(file_name)
            except:
                print(" ERROR: Settings file points to image that does not exist in working directory! Resetting index to 0")

            ## redraw canvas items with updated global values as the given image index
            self.load_img(n)

        self.update_input_widgets()
        return

    def new_box_size(self):
        import re, copy
        global box_size, image_list, n, image_coordinates, img_pixel_size_x, img_pixel_size_y, mrc_pixel_size_x, img_box_size
        user_input = self.input_mrc_box_size.get().strip()
        temp = re.findall(r'\d+', user_input)
        res = list(map(int, temp))

        ## kill function if no entry is given or if value is not even
        if not len(res) == 1 or not isinstance(res[0], int) or not res[0] > 0:
            self.input_mrc_box_size.delete(0,END)
            self.input_mrc_box_size.insert(0, "ang boxsize")
            return
        elif not (res[0] % 2 == 0): # check if value is even
            self.input_mrc_box_size.delete(0,END)
            self.input_mrc_box_size.insert(0, "value must be even")
            return
        ## set the global box_size to the input field value
        box_size = res[0]
        ## redraw boxes by first deleting it then redrawing it
        self.draw_image_coordinates()
        ## revert focus to main canvas
        self.canvas.focus_set()
        return

    def new_mrc_dimensions(self):
        """ Update the global 'mrc_pixel_size_x', 'mrc_pixel_size_y' variables from user input in the main window
        """
        import re ## for use of re.findall() function to extract numbers from strings
        global mrc_pixel_size_x, mrc_pixel_size_y, image_list, n
        user_input = self.input_mrc_dimensions.get().strip()
        temp = re.findall(r'\d+', user_input)
        res = list(map(int, temp))

        if not len(res) == 2:
            self.input_mrc_dimensions.delete(0,END)
            self.input_mrc_dimensions.insert(0, "mrc_X, mrc_Y")
            return
        else:
            mrc_pixel_size_x = res[0]
            mrc_pixel_size_y = res[1]

            ## check for an associated .star file with input coordinates to read
            counter = 0
            star_coordinate_file = ""
            ## find the matching star file if it exists
            for fname in os.listdir(file_dir): ## iterate over the directory
                base_image_name = os.path.splitext(image_list[n])[0] ## get the base name of the .GIF file
                counter = 0
                star_coordinate_file = ""
                if base_image_name in fname and fname[-5:] == ".star": ## find any files that match the base .GIF file name and end in .STAR
                    counter += 1
                    star_coordinate_file = fname
                    if counter > 1: print(">>> WARNING: Multiple .STAR files found for this image (e.g. multiple files match: " + base_image_name + "*.star)")
                    ## This program writes out ..._CURATED.star files, if we find one - use that over all other available .STAR files
                    if star_coordinate_file[-13:] == "_CURATED.star": break
            ## if a star file is found, load its coordinates
            # print(" STAR FILE USED FOR COORDS = ", star_coordinate_file)
            if (star_coordinate_file != ""):
                self.read_coords_from_star(star_coordinate_file)



            ## redraw particle positions and boxsize with the new remapped data
            # self.update_input_widgets()
            # self.load_img(n)
            self.draw_image_coordinates()
        ## revert focus to main canvas
        self.canvas.focus_set()
        return

    def new_angpix(self):
        """ Update the global 'angpix' variable from user input in the main window
        """
        global angpix, box_size
        user_input = self.input_angpix.get().strip()
        try:
            res = float(user_input)
            angpix = res
            ## we need to recalculate the label for box size in angstroms
            # self.box_size_ang.config(text="%s Angstroms" % (box_size * angpix))

        except:
            self.input_angpix.delete(0,END)
            self.input_angpix.insert(0, "angpix")

        ## redraw the picked coordinates
        self.draw_image_coordinates()

        ## revert focus to main canvas
        self.canvas.focus_set()

    def MouseWheelHandler(self, event):
        """ See: https://stackoverflow.com/questions/17355902/python-tkinter-binding-mousewheel-to-scrollbar
        """
        global brush_size, n

        def delta(event):
            if event.num == 5 or event.delta < 0:
                return -2
            return 2

        brush_size += delta(event)

        ## avoid negative brush_size values
        if brush_size <= 0:
            brush_size = 0

        ## draw new brush size
        x, y = event.x, event.y
        x_max = int(x + brush_size/2)
        x_min = int(x - brush_size/2)
        y_max = int(y + brush_size/2)
        y_min = int(y - brush_size/2)
        brush = self.canvas.create_rectangle(x_max, y_max, x_min, y_min, outline="green2", tags='brush')

    def check_if_two_ranges_intersect(self, x0, x1, y0, y1):
        """ For two well-ordered ranges (x0 < x1; y0 < 1), check if there is any intersection between them.
            See: https://stackoverflow.com/questions/3269434/whats-the-most-efficient-way-to-test-two-integer-ranges-for-overlap/25369187
        """
        ## sanity check input
        if (x0 > x1):
            print("ERROR: Incorrect range provided, x0 -> x1 == %s -> %s" % (x0, x1))

        if y0 > y1:
            print("ERROR: Incorrect range provided, y0 -> y1 == %s -> %s" % (y0, y1))

        if x0 <= y1 and y0 <= x1:
            return True
        else:
            return False

    def delete_brush_cursor(self, event):
        global RIGHT_MOUSE_PRESSED, brush_size, image_coordinates, box_size, n, mrc_pixel_size_x, img_pixel_size_x
        if RIGHT_MOUSE_PRESSED:

            x, y = event.x, event.y

            self.canvas.delete('brush')

            x_max = int(x + brush_size/2)
            x_min = int(x - brush_size/2)
            y_max = int(y + brush_size/2)
            y_min = int(y - brush_size/2)

            brush = self.canvas.create_rectangle(x_max, y_max, x_min, y_min, outline="green2", tags='brush')

            ## box_size is a value given in Angstroms, we need to convert it to pixels
            scale_factor = mrc_pixel_size_x / img_pixel_size_x
            angpix_gif = angpix * scale_factor
            gif_half_box_size = int((box_size / angpix_gif)/2) ## since coordinates are given as center, we need to add half the box size to each size of the coordinate

            erase_coordinates = [] # avoid changing dictionary until after iteration complete
            ## find all coordinates that clash with the brush
            if len(image_coordinates) > 0:
                for coord in image_coordinates:
                    if self.check_if_two_ranges_intersect(coord[0] - gif_half_box_size, coord[0] + gif_half_box_size, x_min, x_max): # x0, x1, y0, y1
                        if self.check_if_two_ranges_intersect(coord[1] - gif_half_box_size, coord[1] + gif_half_box_size, y_min, y_max): # x0, x1, y0, y1
                            erase_coordinates.append(coord)
            ## erase all coordinates caught by the brush
            for coord in erase_coordinates:
                del image_coordinates[coord] # remove the coordinate that clashed
            ## redraw particle positions on image
            # self.canvas.delete('particle_positions')
            self.draw_image_coordinates()
        else:
            return

    def on_right_mouse_press(self, event):
        global RIGHT_MOUSE_PRESSED, image_coordinates, brush_size, box_size, n, mrc_pixel_size_x, img_pixel_size_x
        RIGHT_MOUSE_PRESSED = True
        x, y = event.x, event.y
        search_size = int(brush_size/2)
        x_max = int(x + search_size)
        x_min = int(x - search_size)
        y_max = int(y + search_size)
        y_min = int(y - search_size)
        brush = self.canvas.create_rectangle(x_max, y_max, x_min, y_min, outline="green2", tags='brush')

        print("mouse position = ", x, y)
        print("(x min, x max ; y min, y max) = ", x_min, x_max, y_min, y_max)

        ## box_size is a value given in Angstroms, we need to convert it to pixels
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        angpix_gif = angpix * scale_factor
        gif_half_box_size = int((box_size / angpix_gif)/2) ## since coordinates are given as center, we need to add half the box size to each size of the coordinate

        ## in case the user does not move the mouse after right-clicking, we want to find all clashes in range on this event as well
        erase_coordinates = [] # avoid changing dictionary until after iteration complete
        ## find all coordinates that clash with the brush
        if len(image_coordinates) > 0:
            for coord in image_coordinates:
                if self.check_if_two_ranges_intersect(coord[0] - gif_half_box_size, coord[0] + gif_half_box_size, x_min, x_max): # x0, x1, y0, y1
                    if self.check_if_two_ranges_intersect(coord[1] - gif_half_box_size, coord[1] + gif_half_box_size, y_min, y_max): # x0, x1, y0, y1
                        erase_coordinates.append(coord)

        ## erase all coordinates caught by the brush
        for coord in erase_coordinates:
            del image_coordinates[coord] # remove the coordinate that clashed
        ## redraw particle positions on image
        # self.canvas.delete('particle_positions')
        self.draw_image_coordinates()
        return

    def on_right_mouse_release(self, event):
        global RIGHT_MOUSE_PRESSED
        RIGHT_MOUSE_PRESSED = False
        self.canvas.delete('brush') # remove any lingering brush marker
        ## update the .BOX file in case coordinates have changed
        self.save_starfile()
        return

    def on_middle_mouse_press(self, event):
        self.canvas.delete('marker')
        self.canvas.delete('particle_positions')
        return

    def on_middle_mouse_release(self, event):
        global n
        self.draw_image_coordinates()
        # self.load_img(n)
        return

    def save_starfile(self):
        global image_list, n, image_coordinates, box_size, img_box_size, img_pixel_size_x, mrc_pixel_size_x, mrc_pixel_size_y

        # avoid bugging out when hitting 'next img' and no image is currently loaded
        try:
            current_img_base_name = os.path.splitext(image_list[n])[0]

            with open(current_img_base_name + '_CURATED.star', 'w') as f : # NOTE: 'w' overwrites existing file; as compared to 'a' which appends only
                ############
                ## HEADER
                ############
                f.write("\n")
                f.write("data_\n")
                f.write("\n")
                f.write("loop_\n")
                f.write("_rlnCoordinateX #1\n")
                f.write("_rlnCoordinateY #2\n")
                f.write("_rlnClassNumber #3\n")
                f.write("_rlnAnglePsi #4\n")
                f.write("_rlnAutopickFigureOfMerit #5\n")
                f.write("\n")

                ############
                ## BODY
                ############
                for gif_coord in image_coordinates:
                    mrc_coord = image_coordinates[gif_coord]
                    ## new points added on the .GIF with no corresponding .MRC coordinate must interpolate to map the .GIF coordinate onto .MRC
                    ## NOTE: This remapping is imprecise due to uncompression error hence we only do this if it is a 'new_point' in the database
                    if mrc_coord == 'new_point':
                        #### interpolate .MRC coordinate from .GIF position
                        mrc_x, mrc_y = self.gif2star(gif_coord)
                        f.write("%.2f    %.2f   \t -999     -999.0    -999.0 \n" % (mrc_x, mrc_y))
                    else: # if point is not new, we can just write the original corresponding mrc_coordinate back into the file
                        f.write("%.2f    %.2f   \t -999     -999.0    -999.0 \n" % (mrc_coord[0], mrc_coord[1]))
        except:
            pass
        return

    def on_left_mouse_down(self, event):
        global image_coordinates, n

        ## in case the user did not explicitly hit the Enter or Return button after editing the boxsize or pixel size entries, refresh their inputs
        self.new_angpix()
        self.new_box_size()

        mouse_position = event.x, event.y

        ## when clicking, check the mouse position against loaded coordinates to figure out if the user is removing a point or adding a point
        if self.is_clashing(mouse_position): # this function will also remove the point if True
            print("CLASHING")
            pass
        else:
            print("Add coordinate: x, y =", mouse_position[0], mouse_position[1])
            x_coord = mouse_position[0]
            y_coord = mouse_position[1]
            image_coordinates[(x_coord, y_coord)] = 'new_point'
        ## redraw data on screen
        # self.load_img(n)
        self.draw_image_coordinates()
        return

    def is_clashing(self, mouse_position):
        """ mouse_position = tuple of form (x, y)
        """
        global image_coordinates, img_box_size, n, box_size

        ## Calculate the boundaries to use for the clash check
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        angpix_gif = angpix * scale_factor
        gif_box_width = box_size / angpix_gif ## this is the pixel size of the gif image, we can use this to calculate the size of the box to draw
        gif_box_halfwidth = int( gif_box_width / 2 )

        for (x_coord, y_coord) in image_coordinates:
            # print(" CLASH TEST :: mouse_position = ", mouse_position, " ; existing coord = " , x_coord, y_coord)
            ## check x-position is in range for potential clash
            if x_coord - gif_box_halfwidth <= mouse_position[0] <= x_coord + gif_box_halfwidth:
                ## check y-position is in range for potential clash
                if y_coord - gif_box_halfwidth <= mouse_position[1] <= y_coord + gif_box_halfwidth:
                    ## if both x and y-positions are in range, we have a clash
                    del image_coordinates[(x_coord, y_coord)] # remove the coordinate that clashed
                    return True # for speed, do not check further coordinates (may have to click multiple times for severe overlaps)
        return False

    def mark_img(self):
        """ When called, this function updates a list of file names with the current active image. If the current
            img is already marked, it will be 'unmarked' (e.g. removed from the list)
        """
        global n, image_list, marked_imgs
        # current_img = image_list[n]
        current_img = os.path.splitext(image_list[n])[0] ## get the base name of the .GIF file
        # print("Marked imgs = ", marked_imgs)
        print("Mark image = ", current_img)

        if not current_img in marked_imgs:
            marked_imgs.append(current_img)
            self.load_img(n) ## after updating the list, reload the canvas to show a red marker to the user
        else:
            marked_imgs.remove(current_img)
            self.load_img(n) ## reload the image canvas to remove any markers
        return

    def select_all(self, widget):
        """ This function is useful for binding Ctrl+A with
            selecting all text in an Entry widget
        """
        return widget.select_range(0, END)

    def load_file(self):
        """ Permits the system browser to be launched to select an image
            form a directory. Loads the directory and file into their
            respective variables and returns them
        """
        global file_dir, file_name, image_list, n, marked_imgs
        # See: https://stackoverflow.com/questions/9239514/filedialog-tkinter-and-opening-files
        fname = askopenfilename(parent=self.master, initialdir=".", title='Select file', filetypes=(
                                            ("All files", "*.*"),
                                            ("Graphics interchange format", "*.gif"),
                                            ("Joint photographic experts group", "*.jpeg;*.jpg")
                                            ))
        if fname:
            try:
                # extract file information from selection
                file_w_path = str(fname)
                file_dir, file_name = os.path.split(str(fname))
                print("File selected: "+ file_name)
                print("Active directory: "+ file_dir)

                # erase any previous image list and repopulate it with the new directory
                image_list = []
                image_list = self.images_in_dir(file_dir)

                # erase any marked image list or particle coordinates loaded into RAM
                marked_imgs = []

                # find the index of the selected image in the new list
                n = image_list.index(file_name)

                ## redraw canvas items with updated global values as the given image index
                self.load_img(n)

            except:
                showerror("Open Source File", "Failed to read file\n'%s'" % fname)
            return

    def reset_globals(self):
        global image_coordinates, img_box_size
        image_coordinates = {}
        img_box_size = 0
        return

    def next_img(self, direction):
        """ Increments the variable 'n' based on the direction given to the function.
        """
        global n, image_list, file_dir, image_coordinates, img_pixel_size_x, img_pixel_size_y

        ## update the labels for the gif pixel dimensions
        if IMAGE_LOADED:
            # img_pixel_size_x = self.current_img.width()
            # img_pixel_size_y = self.current_img.height()
            self.img_size.config(text="%s, %s px" % (img_pixel_size_x, img_pixel_size_y))
            # print("img_pixel_size_x = ", img_pixel_size_x, " img_pixel_size_y = ", img_pixel_size_y)

        ## save particles into boxfile, if coordinates are present
        if len(image_coordinates) > 0 :
            self.save_starfile()

        if file_dir == '.':
            file_dir=os.getcwd()
            try:
                self.current_dir.config(text=file_dir + "/")
            except:
                pass
        if direction == 'right':
            n += 1
            # reset index to the first image when going past the last image in the list
            if n > len(image_list)-1 :
                n = 0
        if direction == 'left':
            n -= 1
            # reset index to the last image in the list when going past 0
            if n < 0:
                n = len(image_list)-1

        # update image list in case files have been added/removed
        image_list = []
        image_list = self.images_in_dir(file_dir)

        ## clear global variables for redraw
        self.reset_globals()

        ## load image with index 'n'
        self.load_img(n)
        return

    def load_img(self, index, input_img = None):
        """ Load image with specified index
        PARAMETERS
            index = int(); tied to global 'n' variable, indicating which image to load from the list found in the directory
            input_img = np.array; optional grayscale image (0 - 255) to load instead of using the index
        RETURNS
            Void
        """
        global n, image_list, marked_imgs, img_pixel_size_x, img_pixel_size_y, IMAGE_LOADED, image_coordinates, current_im_data

        ## force a refresh on all canvas objects based on changing global variables
        self.canvas.delete('marker')
        self.canvas.delete('particle_positions')

        image_w_path = file_dir + "/" + image_list[n]

        # update label widget
        self.input_text.delete(0,END)
        self.input_text.insert(0,image_list[n])

        ## check if an eplicit image was passed in, otherwise load the image as usual
        if input_img is None:
            # load image onto canvas object using PhotoImage
            PIL_image = Image.open(image_w_path).convert('L')
            self.current_img = ImageTk.PhotoImage(PIL_image)
            current_im_data = np.asarray(PIL_image)
        else:
            ## load the supplied image
            PIL_image = Image.fromarray(input_img) #.convert('L')
            self.current_img = ImageTk.PhotoImage(PIL_image)
            current_im_data = input_img


        # self.current_img = PhotoImage(file=image_w_path)
        self.display = self.canvas.create_image(0, 0, anchor=NW, image=self.current_img)
        self.canvas.display = self.display

        IMAGE_LOADED = True;

        # resize canvas to match new image
        x,y = self.current_img.width(), self.current_img.height()
        self.canvas.config(width=x, height=y)
        img_pixel_size_x = x
        img_pixel_size_y = y

        ## update widget displaying pixel size of .GIF file
        self.img_size.config(text="%s, %s px" % (img_pixel_size_x, img_pixel_size_y))

        base_image_name = os.path.splitext(image_list[n])[0] ## get the base name of the .GIF file

        ## add an inset red border to the canvas depending if the file name exists in a given list
        if base_image_name in marked_imgs:
            marker_rect = self.canvas.create_rectangle(x-10,y-10, 10, 10, outline='red', width=10, tags='marker')

        ## empty any pre-existing image coordinates in memory
        # image_coordinates = {}

        if len(image_coordinates) == 0: ## avoid overwriting an existing image_coordinates dictionary if it is already present
            counter = 0
            star_coordinate_file = ""
            ## find the matching star file if it exists
            for fname in os.listdir(file_dir): ## iterate over the directory
                if base_image_name in fname and fname[-5:] == ".star": ## find any files that match the base .GIF file name and end in .STAR
                    counter += 1
                    star_coordinate_file = fname
                    if counter > 1: print(">>> WARNING: Multiple .STAR files found for this image (e.g. multiple files match: " + base_image_name + "*.star)")
                    ## This program writes out ..._CURATED.star files, if we find one - use that over all other available .STAR files
                    if star_coordinate_file[-13:] == "_CURATED.star": break
            ## if a star file is found, load its coordinates
            # print(" STAR FILE USED FOR COORDS = ", star_coordinate_file)
            if (star_coordinate_file != ""):
                self.read_coords_from_star(star_coordinate_file)

        self.update_input_widgets()
        self.draw_image_coordinates()
        return

    def is_image(self, file):
        """ For a given file name, check if it has an appropriate suffix.
            Returns True if it is a file with proper suffix (e.g. .gif)
        """
        image_formats = [".gif", ".jpg", ".jpeg"]
        for suffix in image_formats:
            if suffix in file:
                return True
        return False

    def images_in_dir(self, path) :
        """ Create a list object populated with the names of image files present
        """
        global image_list
        for file in sorted(os.listdir(path)):
            if self.is_image(file):
                image_list.append(file)
        return image_list

    def choose_img(self):
        """ When called, finds the matching file name from the current list and
            loads its image and index
        """
        global image_list, n
        user_input = self.input_text.get().strip()
        if user_input in image_list:
            n = image_list.index(user_input)
            self.load_img(n)
        else:
            self.input_text.delete(0,END)
            self.input_text.insert(0,"File not found.")
        self.canvas.focus_set()

    def write_marked(self, file="marked_imgs.txt"):
        """ Write marked files (mark files with hotkey 'd') into a file
        """
        ## save a settings as well
        self.save_settings()
        global marked_imgs
        ## if present, determine what entries might already exist in the target file (e.g. if continuing from a previous session)
        existing_entries = []
        if os.path.exists(file):
            with open(file, 'r') as f :
                for line in f:
                    existing_entries.append(line.strip())

        # ## write new marked images into file, if any present
        # with open(file, 'a') as f :
        #     for marked_img in marked_imgs:
        #         if not marked_img in existing_entries:
        #             f.write("%s\n" % marked_img)
        #             print("Entry written to %s: %s" % (file, marked_img))
        #         else:
        #             print("Entry already present in file: %s" % marked_img)

        ## write new marked images into file, if any present
        with open(file, 'w') as f :
            counter = 0
            for marked_img in marked_imgs:
                counter += 1
                ## write all marked_img names into the file from RAM
                f.write("%s\n" % marked_img)
            print(" >> %s entries written into 'marked_imgs.txt'" % counter)

        ## indicate which images were dropped from the previous file
        for existing_entry in existing_entries:
            if not existing_entry in marked_imgs:
                print(" ... %s was removed from previous entries after rewriting file" % existing_entry)

        ## also save current image particle coordinates if they are present
        if len(image_coordinates) > 0:
            self.save_starfile()

    def load_marked_filelist(self):
        global marked_imgs, n

        ## load selected file into variable fname
        fname = askopenfilename(parent=self.master, initialdir="./", title='Select file', filetypes=( ("File list", "*.txt"),("All files", "*.*") ))
        if fname:
            try:
                ## extract file information from selection
                logfile_path = str(fname)

                ## parse logfile into program
                with open(logfile_path, 'r') as file_obj :
                    for line in file_obj:
                        ## ignore header lines indicated by hash marks
                        if line[0] == '#':
                            continue
                        ## parse each line with space delimiter into a list using .split() function (e.g. img_name note -> ['img_name', 'note'])
                        column = line.split()
                        ## eliminate empty lines by removing length 0 lists
                        if len(column) == 0:
                            continue
                        ## in cases where multiple entries exist per line, take only the first entry
                        img_name = column[0]
                        # mic_name = os.path.splitext(column[0])[0] # os module path.splitext removes .MRC from input name

                        ## skip adding entry to marked list if already present (e.g. duplicates)
                        if img_name in marked_imgs:
                            continue
                        ## write entry into dictionary
                        marked_imgs.append(img_name)

            except:
                showerror("Open Source File", "Failed to read file\n'%s'" % fname)

            self.load_img(n) ## reload image in case it has now been marked

            return

    def draw_image_coordinates(self):
        """ Read the global variable list of coordinates with gif and box files associated via a dictionary format, draw all gif coordinates present (regardless if they have associated box coordinates.
        """
        global image_coordinates, box_size, img_pixel_size_x, mrc_pixel_size_x, angpix

        ## delete any pre-existing coordinates if already drawn
        self.canvas.delete('particle_positions')

        ## box_size is a value given in Angstroms, we need to convert it to pixels
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        angpix_gif = angpix * scale_factor
        gif_box_width = box_size / angpix_gif ## this is the pixel size of the gif image, we can use this to calculate the size of the box to draw
        gif_box_halfwidth = int( gif_box_width / 2 )

        # print(" ANGPIX = ", angpix, " ; GIF_ANGPIX = " , angpix_gif, " ; SCALE FACTOR = ", scale_factor)

        for coordinate in image_coordinates:
            ## each coordinate is the center of a box, thus we need to offset by half the gif_box_width pixel length to get the bottom left and top right of the rectangle
            x0 = coordinate[0] - gif_box_halfwidth
            y0 = coordinate[1] - gif_box_halfwidth
            x1 = coordinate[0] + gif_box_halfwidth
            y1 = coordinate[1] + gif_box_halfwidth #y0 - img_box_size # invert direction of box to take into account x0,y0 are at bottom left, not top left
            self.canvas.create_rectangle(x0, y0, x1, y1, outline='red', width=1, tags='particle_positions')

    def header_length(self, file):
        """ For an input .STAR file, define the length of the header and
            return the last line in the header. Header length is determined by
            finding the highest line number starting with '_' character
        """
        with open(file, 'r') as f :
            line_num = 0
            header_lines = []
            for line in f :
                line_num += 1
                first_character = ""
                line = line.strip() # remove empty spaces around line
                line_to_list = line.split() # break words into indexed list format
                # ignore empty lines
                if len(line) == 0 :
                    continue
                first_character = list(line_to_list[0])[0]
                if first_character == '_':
                    header_lines.append(line_num)
                    # if VERBOSE:
                    #     print("Line # %d = " % line_num, end="")
                    #     print(line, " --> ", line_to_list, sep=" ")
            return max(header_lines)

    def find_star_column(self, file, column_type, header_length) :
        """ For an input .STAR file, search through the header and find the column numbers assigned to a given column_type (e.g. 'rlnMicrographName', ...)
        """
        column_num = None # initialize variable for error handling
        with open(file, 'r') as f :
            line_num = 0
            for line in f :
                line_num += 1
                ## extract column number for micrograph name
                if column_type in line :
                    column_num = int(line.split()[1].replace("#",""))
                ## search header and no further to find setup values
                if line_num >= header_length :
                    ## handle error case where input .STAR file is missing a necessary rlnColumn type
                    if column_num is None :
                        print("Input .STAR file: %s, is missing a column for: %s" % (file, column_type) )
                        sys.exit()
                    else:
                        # if VERBOSE:
                            # print("Read though header (%s lines total)" % header_length)
                            # print("Column value for %s is %s" % (column_type, column_num))
                        return column_num

    def find_star_info(self, line, column):
        """ For a given .STAR file line entry, extract the data at the given column index.
            If the column does not exist (e.g. for a header line read in), return 'False'
        """
        # break an input line into a list data type for column-by-column indexing
        line_to_list = line.split()
        try:
            column_value = line_to_list[column-1]
            # if VERBOSE:
            #     print("Data in column #%s = %s" % (column, column_value))
            return column_value
        except:
            return False

    def auto_contrast(self):
        """
        """
        global image_coordinates, script_path, file_dir, image_list, n, current_im_data
        try:
            sys.path.append(script_path)
            import image_handler #as image_handler
        except :
            print("Abort auto_contrast :: Check if image_handler.py script is in same folder as this script and runs without error (i.e. can be compiled)!")
            return

        # ## get the current image name with full path
        # image_w_path = file_dir + "/" + image_list[n]
        #
        # ## use Pillow to open the image as a grayscale
        # PIL_image = Image.open(image_w_path).convert("L")
        # ## convert the image data to a numpy array for processing
        # im = np.array(PIL_image)
        # print(type(im), im.shape, "pixels", ", intensity (min, max) = ", np.min(im), np.max(im))

        im = current_im_data
        ## use the image processing functions to modify the desired img
        im = image_handler.auto_contrast(im)

        ## load the modified img onto the canvas
        current_im_data = im
        self.load_img(n, im)
        return

    def contrast_by_selected_particles(self):
        """
        """
        global image_coordinates, script_path, file_dir, image_list, n, mrc_pixel_size_x, img_pixel_size_x, angpix, box_size, current_im_data
        try:
            sys.path.append(script_path)
            import image_handler #as image_handler
        except :
            print("Abort auto_contrast :: Check if image_handler.py script is in same folder as this script and runs without error (i.e. can be compiled)!")
            return

        ## box_size is a value given in Angstroms, we need to convert it to pixels
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        angpix_gif = angpix * scale_factor
        gif_box_width = int(box_size / angpix_gif) ## this is the pixel size of the gif image, we can use this to calculate the size of the box to draw

        # ## get the current image name with full path
        # image_w_path = file_dir + "/" + image_list[n]
        #
        # ## use Pillow to open the image as a grayscale
        # PIL_image = Image.open(image_w_path).convert("L")
        # ## convert the image data to a numpy array for processing
        # im = np.array(PIL_image)
        # print(type(im), im.shape, "pixels", ", intensity (min, max) = ", np.min(im), np.max(im))
        im = current_im_data
        ## extract the particle images from the centered coordinates
        extracted_imgs = image_handler.extract_boxes(im, gif_box_width, image_coordinates, DEBUG = True)
        min, max = image_handler.find_intensity_range(extracted_imgs)
        ## whiten outliers so we can apply new contrast to it
        im = image_handler.whiten_outliers(im, min, max)

        ## use the image processing functions to modify the desired img
        im = image_handler.sigma_contrast(im, 1) ## let the user adjust the sigma value?
        # im = image_handler.gaussian_blur(im, 1.5)

        ## load the modified img onto the canvas
        current_im_data = im
        self.load_img(n, im)

        return

    def gaussian_blur(self):
        global n, current_im_data
        try:
            sys.path.append(script_path)
            import image_handler #as image_handler
        except :
            print("Abort auto_contrast :: Check if image_handler.py script is in same folder as this script and runs without error (i.e. can be compiled)!")
            return
        im = current_im_data
        im = image_handler.gaussian_blur(im, 1.5)
        current_im_data = im
        self.load_img(n, im)
        return


##########################
### RUN BLOCK
##########################
if __name__ == '__main__':
    import numpy as np

    ## Get the execution path of this script so we can find modules in its root folder, if necessary
    script_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    print("Exectuable path = ", script_path)

    n=0
    img_on_save = ''

    IMAGE_LOADED = False # Flag to check if an image is loaded (to avoid throwing errors)
    current_im_data = None ## np array of grayscale image current being displayed

    RIGHT_MOUSE_PRESSED = False # Flag to implement right-mouse activated brush icon

    # initialize global values here
    image_list = []
    file_name = ''
    file_dir = '.'

    marked_imgs = []

    image_coordinates = {} # dictionary in format, { (gif_x, gif_y) : (mrc_x, mrc_y), ... }, points given as top left, bottom left corner of box, respectively
    img_box_size = 100 # how many pixels is the width and height of a particle box
    box_size = 100 # box size in .box file

    autopick_min_distance = int(box_size / 2)
    autopick_threshold = 0.1
    autopick_blur = 2
    autopick_refinement_method = ""
    autopick_refine_threshold = 0.1

    ## gif image dimensions are updated every time we load a new image, these globals are then used by other functins for scaling between .MRC pixel dimensions
    img_pixel_size_x = 0
    img_pixel_size_y = 0

    # box_size_angstroms = 100 # Angstroms # adjust this with a widget
    angpix = 1.94 # angstroms per pixel in MRC file from which GIF came from # adjust with widget
    mrc_pixel_size_x = 4092
    mrc_pixel_size_y = 4092

    brush_size = 20 # size of erase brush

    root = Tk()
    app = Gui(root)
    root.mainloop()
