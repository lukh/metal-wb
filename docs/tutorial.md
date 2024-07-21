

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


### Via Bevels property

It is my favorite for simple frame..

Let's hide everything except the first frame we made...

![alt text](tutorial.imgs/40-show-first-frame.png)

1. Select one of the profile, and in the property section, go for Bevel Start/End Cut 1/2

![alt text](image.png)

There are 4 entries (Start / End Cut1 Cut2)

That allows you to create bevels in the two axis, at the start or end of the profile.

Negative angles works, and must be used to compensate directions.

You can batch-modify that, by selecting all the profiles....

![alt text](tutorial.imgs/42-batchs-bevels.png)

And Voila ! a square frame !


### Via Corners function

Let's show the other base frame ...

![alt text](tutorial.imgs/50-base-config.png)

This method take longer, but allows for more complexs forms...

We first must add offsets to the existing profiles...  (offsets are cool because it adds up to the dimension of the sketch !)

1. add Offset (batch or single...)

![alt text](tutorial.imgs/51-add-offset.png)

2. Unselect all objects, and click on create corner

![alt text](tutorial.imgs/52-create-corner.png)

![alt text](tutorial.imgs/53-create-corner.png)

Select the end miter option

![alt text](tutorial.imgs/53-end-miter.png)

3. In the 3D view, select the object (profile you want to cut)

![alt text](tutorial.imgs/54-select-one.png)

and click on the "Trimmed Body" "+" sign. It will add the profile to the body trimmed

![alt text](tutorial.imgs/55-add-to-trimmed.png)


The profile will hide, helping you selecting the trimming boundary.

4. select the face of the profile you want to trim with the first profile, and add to trimming boundary into the corner manager.

![alt text](tutorial.imgs/56-add-to-boundary.png)

![alt text](tutorial.imgs/57-almost-ready.png)

5. Press ok to validate.

Now, you have one of the profile that has a nice miter joint.

You have to do it again, swapping trimmed body and boundary to maake the other profile

![alt text](tutorial.imgs/58-do-it-again.png)

Notice the Corner objects ! They are build from "Square objects" from MetalWB.


### More complex Corners

Let's finish the 3 others corners of the second frame...

![alt text](tutorial.imgs/60-startwith.png)

![alt text](tutorial.imgs/61-bad-joint.png)

When everything is showed again, you can see the vertical profiles are not cut as they should...

Let's open again the corner manager, selecting "end trim"

![alt text](tutorial.imgs/62-endtrim.png)

1. Select the vertical profile first, add it to the trimmed body with the plus button,
2. Select the face of the profile you want to cut with.. (here, I add to move the view and select the bottom **face**)

![alt text](tutorial.imgs/63-select-the-face.png)


You can change the cut type: straight or following the other profile.

![alt text](tutorial.imgs/64-cuttype-1.png)

![alt text](tutorial.imgs/64-cuttype-2.png)



## Organizing Objects

That's the bad part.

I find the tree view messy. Really messy.

### Part Container

I often use Part container for grouping profiles, sketchs, etc.

![alt text](tutorial.imgs/70-part-container.png)

![alt text](tutorial.imgs/71-part-container.png)

You need to drag only one profile to the container... I don't know why, but FreeCAD is not happy about a group drag.

Sometime parts and profile get out of the Part Container.



### Fusion

One can fuse profiles together.

![alt text](tutorial.imgs/72-fusion.png)

![alt text](tutorial.imgs/72-fusion-done.png)

It allows to group objects. 


## Using profiles in Part Design... ie, making holes !

To use all of theses profiles in PartDesign, for instance, to make holes... in it.. !

you need to use a fusion of the profile, and create a body...

![Body](tutorial.imgs/80-body.png)

1. Drag and drop the fusion into the body.

![base feature](tutorial.imgs/81-basefeature.png)

2. Now, you have a standard Part design Body...

You can map a sketch to any face, and use Part design to do whatever you want !

![Making Holes](tutorial.imgs/82-making-holes.png)

![Holes Made](tutorial.imgs/83-holes-made.png)