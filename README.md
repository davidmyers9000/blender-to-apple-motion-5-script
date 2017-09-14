# blender-to-apple-motion-5-script
https://blenderartists.org/forum/showthread.php?227090-Blender-to-Apple-Motion-export-script

Disclaimer: I did not create this script, just wanted to host it via github in case the link on blenderartists goes down. See the original link in the description

# Blender to Apple Motion export script

osxrules:

> Similar to the Maya Ascii script, I have developed one for Apple's Motion program. Motion has a number of nice features and is very cheap. It is £35 as opposed to £750+ for After Effects. It's also entirely hardware-accelerated so is fairly quick at rendering. It also integrates with Final Cut Pro so you can make up Motion templates with drop-zones and reuse clips.
> 
> The script is available here:
> 
> http://www.dev-art.co.uk/files/motion_camera_tracking.py.zip
> 
> There's a video that follows showing how the process works between Cinema 4D and Motion:
> 
> http://provideocoalition.com/index.php/motiongraphicsvizfx/video/cinema4d_finally_brings_3d_to_motion/
> 
> You should be able to achieve the same thing with this Blender script.
> 
> If you run the script in the text editor, it will put an entry into the file > export menu to Apple Motion (.motn). When you select this, it will ask for an export location and save out a Motion project file with a .motn extension.
> 
> You would render your Blender animation out with appropriate masks and save it in a format that Motion will recognise. Then open the .motn file by double-clicking. To get round some stability issues with IDs in the file, it is setup as a Motion 3 file so will ask to upgrade it, which is fine - when you save the file, it adds all the required data back in. Hopefully this means it will work in Motion 3, 4 and 5 but I only tested it in version 5.
> 
> You import your rendered clip into Motion and drop it into the scene on a new layer and set this layer to not be a 3D layer. Any objects you add into the scene as 3D layers should then follow the camera movement and match the rendered footage.
> 
> This export is a bit different from the Maya one and I was able to exclude more redundant keyframes so should hopefully be faster and less memory intensive but naturally with changes, there's a chance it's messed up some things so if you can test it out and let me know if anything has gone wrong, I'll try and get it to a state where it's reliable to use.
