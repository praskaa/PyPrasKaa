# Bundle Context

<aside>
<img src="ic_01_idea.png" alt="ic_01_idea.png" width="40px" /> **Command Availability**: Revit commands use standard `IExternalCommandAvailability` class to let Revit know if they are available in different contexts. For example, if a command needs to work on a set of elements, it can tell Revit to deactivate the button unless the user has selected one or more elements.

</aside>

In pyRevit, command availability is set through the `context` key in bundle file. Currently, pyRevit support three types of command availability types.

```yaml
# Tools are active even when there are no documents available/open in Revit
context: zero-doc

# Tool activates when at least one element is selected
context: selection

# Tool activates when all selected elements are of the given category, or categories
context: <category>

context:
	- <category>
  - <category>
```

The `selection` and `zero-doc` contexts are pretty easy to follow

## Select Element Category Context

If `<category>` starts with `OST_` (e.g. `OST_Doors`), comparison will be made using [BuiltInCategory](https://apidocs.co/apps/revit/2020/ba1c5b30-242f-5fdc-8ea9-ec3b61e6e722.htm). The builtin category names are language-agnostic, so your tool would follow the correct context, no matter what Revit language is being used. `<category>` can also be any of the standard Revit element categories. You can use the **pyRevit → Spy → List Elements**, to list the standard category names.

Here are a few examples:

```yaml
# Tool activates when all selected elements are of the given category
context: Doors
context: Walls
context: Floors

context: OST_Doors

context:
  - Space Tags
  - Spaces
```

## Active Document Context

Bundle can also require a specific type of document to be active. Here are the available options

```yaml
context: doc-project                    # bundle is active when the active document is a Project
context: doc-workshared                 # bundle is active when the active document is a Workshared Project
context: doc-cloud                      # bundle is active when the active document is a Cloud Project (Revit >=2019.1)
context: doc-family                     # bundle is active when the active document is a Family
```

## Active View Context

Bundle can also require a specific type of active view to be active. Here are the available options

```yaml
context: active-drafting-view           # bundle is active when the active view is a Drafting view
context: active-plan-view               # bundle is active when the active view is any Plan
context: active-floor-plan              # bundle is active when the active view is a Floor Plan
context: active-rcp-plan                # bundle is active when the active view is a Reflected Ceiling Plan
context: active-structural-plan         # bundle is active when the active view is a Structural Plan
context: active-area-plan               # bundle is active when the active view is an Area Plan
context: active-elevation-view          # bundle is active when the active view is an Elevation
context: active-section-view            # bundle is active when the active view is a Section
context: active-3d-view                 # bundle is active when the active view is a 3D view
context: active-sheet                   # bundle is active when the active view is a Sheet
context: active-legend                  # bundle is active when the active view is a Legend
context: active-schedule                # bundle is active when the active view is a Schedule
```

Finally, the various context types can be combined together for more complex contexts. Here are some examples

```yaml
context:
	- selection
	- active-section-view

context:
	- walls
	- columns
	- active-plan-view
```

## Advanced Contexts

You can define more specific context conditions using `any`, `all`, and `exact` conditions. You can also use `not_any`, `not_all`, and `not_exact` to reverse the condition. Here are a series of examples:

```yaml
context:
	- active-floor-plan
	- any:
	  - OST_Walls
	  - OST_Floors

```

```yaml
context:
	any:
    - active-floor-plan
    - active-rcp-plan
  all:
    - OST_Walls
    - OST_Floors
```

```yaml
context:
	- doc-project
  - exact:
    - OST_Walls
    - OST_Floors
```

```yaml
context:
	- doc-workshared
	- all:
		- OST_Walls
    - OST_Floors
```

```yaml
context:
  not_any:
    - OST_Walls
    - OST_TextNotes
```

```yaml
context:
  not_exact:
    - OST_Walls
    - OST_TextNotes
```