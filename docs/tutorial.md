

# FreeCAD MetalWB Tutorial


## Create the skeleton

We are going to create a simple frame.

1. In a new file, switch to the MetalWB workbench.

2. Create a sketch, and select orientation (XY for instance)

![Create Sketch](tutorial.imgs/00-create-sketch.png)

![Select Orientation](tutorial.imgs/01-select-orientation.png)


3. Draw a simple square in the sketch... it will be our skeleton

![Create Skeleton](tutorial.imgs/02-create-frame-skeleton.png)

4. Close the Sketch edit mode.

## Create the frame

1. Lauch the Warehouse Profile tool.

![warehouse profile](tutorial.imgs/10-warehouse-profiles.png)

![warehouse profile](tutorial.imgs/10-warehouse-profiles-modal.png)

2. Select a profile from the list

![profiles choice](tutorial.imgs/11-profiles-family.png)


You can change the size just below the family, the tool has a lot of predefined profile, you can also change the parameters...

![profile choice](tutorial.imgs/12-profile-square-20x2.png)


3. In the 3D View, select edges to apply the profile creation:

![Edge Selection](tutorial.imgs/13-edge-selection.png)

4. And press OK in the warehouse profile window... (then, cancel to close the window !)

![Profiles](tutorial.imgs/14-profiles-done.png)
![Zoom in profile](tutorial.imgs/14-zoom-on-profile.png)

![Tree](tutorial.imgs/14-profile-tree.png) 


**And voila ! You have your first frame !**


## Going 3D... Making a cube !

We can build more complexe shapes, and there are severals ways of doing it.

### More Sketchs !

We can add more sketchs into our project:

1. Create a new Sketch
2. Select the same orientation as the previous one (XY)
3. Draw a square the same size and placement as the previous one.


4. Now, change the position of the sketch:
![Base Placement](tutorial.imgs/20-sketch-base-placement.png)

![Sketch moved !](tutorial.imgs/20-sketch-base-placement-2.png)

And the new sketch is 400mm on top of the first one !

You can therefore use Warehouse profile again to create another square frame !

![Stacked Frames](tutorial.imgs/21-stacked-frames.png)

### Parametric Line

You can create parametrics lines for joining two vertexes (points), theses lines can be used with Warehouse Profile as well...

1. one can hide profiles objects with [Space Bar] (it allows to see the sketches)

![Hide profile](tutorial.imgs/22-hide-profiles.png)

2. Selects vertexes

![Select Vertexes](tutorial.imgs/23-select-vertexes.png)


3. Create Parametric Line

![Create parametric line](tutorial.imgs/24-create-parametric-line.png)
![alt text](tutorial.imgs/25-parametric-line.png)


You can therefore use Warehouse profile again to create another square frame !

4. Open Warehouse Profile, select the profile you want
5. Select the Parametric line, click OK then Cancel..

![alt text](tutorial.imgs/26-cube-done.png)



### More Sketchs / Part2 !

There is another ways to add sketchs, that allows to do more complicated stuff...

Sometime you want add a sketch to a specific place, and link it to another sketch. (If you modify the first Sketch, then the second will follow, hopefully)

This is not possible with the Position / Base Placement, that is an absolute position.

We are going to "Map" the sketch to something else.

1. Create a new Sketch, and set orientation to: YZ

I added a circle so you can see where it is..
![alt text](tutorial.imgs/30-mapmode-sketch.png)

2. Click on the map mode property:

![alt text](tutorial.imgs/31-mapmode.png)

![alt text](tutorial.imgs/32-mapmode-dialog.png)


You can change the map mode, selecting faces, vertexes and edges...

![alt text](tutorial.imgs/33-mapmode.png)

Here, our circle is in a new plan, the one at the top left of the screen...

There are a lot of options here. You can then edit the sketch, and create more line and frames...

## Bevels and corners.

As you can see, the junctions are not that good (yet !). The profiles are centered on the skeleton, and stops right at the end of the edges.

We are going to make corners, and bevels. There are two methods for that.
