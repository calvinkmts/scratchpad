# Python Class

## Background 

Python class, have few options, dataclass, pydantic and lastly I found attrs. 

## Preference

Always go for dataclass, if not enough (being cumbersome) go for attrs.

The idea attrs is more lightweight than pydantic, and the 3rd party library cattrs, have a way for me that is make sense to structure/un-structure object into json or vice versa (I believe we call it marshal and unmarshal in golang). 

More detail of the lightweight-ness of atrrs is that we don't get bloated with many functions that we probably don't need. 

## Case against pydantic

If you take a look at the pydantic sites, it is developed more for validation library so requiring it for creating class (not a validation object) for me is not really the way I want to go.

