# em_dataset_curator
Designed to be used after running `mrc2img.py` across a dataset to generate small, portable reference dataset of `.jpg` images from which a user can quickly curate micrograph quality and particle coordinates. `em_dataset_curator.py` provides a simple GUI interface that handles all image loading and curation markup. Accessory scripts include a very simple autopicker (`peak_finder.py`) and scripts for common post-curation activities (such as using the `marked_imgs.txt` file to unselect a images in a `relion` processing pipeline). Most of these accessory tools remain a work-in-progress.

## Usage

### `em_dataset_curator.py`
Run this script in a directory of `.jpg` images (created from motion corrected `.mrc` files) and curate your dataset. If a `.star` file is present with the same basename as the image, this program will attempt to load all coordinates from it. Coordinates after loading/picking are always saved with the suffix `_CURATED.star` once navigating away from an image or running a save function call. Once made, the `_CURATED.star` file will always be loaded over all other matches in the current directory. The goal of this program is to quickly let the user assess image quality and assess/modify autopicking results:
#### Buttons
`d ` = mark image (a red box will appear over margins of image).

`Ctrl + S` = save a `marked_imgs.txt` file in working directory with a list of marked images. 

`Left click` = Select particle (or, remove selected particle if already selected).
`Middle click` = While toggled, hide all markup to see image below.
`Right click` = Activate erase brush, hold & drag to erase on-the-fly.
`Mouse scrollwheel` = Increase/decrease eraser tool brush size

#### (i) Method for curating micrographs:
As you are navigating through a dataset, you can mark an image (often for removal) using `d`, or unmark it if it is already marked. Progress can be saved with `Ctrl + S`, which writes out a `marked_imgs.txt` file containing all micrographs. If a `marked_imgs.txt` file is present when opening the program, it will attempt to load that data into the session.
#### (i) Method for picking/curating particle coordinates:
Clicking anywhere on an image will place a box at that coordinate. You will have to adjust the options in the `Settings` panel for the size & position to be accurate. Since untransformed `.mrc` coordinates are used, it is necessary for the user to input the pixel size of the original image to correctly map all coordinates onto the binned/resized `.jpg` image. 
Clicking on a box that is already present will remove it. Right clicking will activate eraser mode, displaying a green box that will remove any coordinates underneath it. Eraser mode remains active as the user drags with right-click active, permitting very quick clean up of micrograph areas with bad picks (e.g. carbon/gold edge). The mousewheel allows the eraser size to increase/decrease. Finally, clicking the mousewheel temporarily hides all boxes from the image, allowing the user to see the underlying image with more clarity.

-----
## WIP/To Do
### `marked_imgs_to_backup_selection.py`
Intended to take in a `marked_imgs.txt` file and a `micrographs_ctf.star` file and return a `backup_selection.star` file that can be copied into a `ManualPick` job as a way to remove micrographs from a dataset cleanly. 


### `remove_particles_from_marked_imgs.py`
Intended to take in a `marked_imgs.txt` file and a `particles.star` file and return a new `particles.star` file with particles from marked micrographs removed. 

-----
## Dependencies
Dependencies for these scripts are designed to be easy to install using `pip`.

#### NumPy
Calculation & array handling in python. See: (https://numpy.org/)

`pip install numpy`

#### Pillow (PIL fork)  
Handles image formats for .JPG, .PNG, .TIF, .GIF. See: (https://pillow.readthedocs.io/en/stable/)  

`pip install --upgrade Pillow`

#### imageio


`pip install imageio`

#### SciPy


`pip install scipy`

#### matplotlib


`pip install matplotlib`

#### skimage


`pip install skimage`

#### tkinter
Usually bundled with `python` installations by default. But if not, can be installed on `ubuntu` via:
`sudo apt install python3-tk`


