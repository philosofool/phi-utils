"""Classes and functions to handle data cleaning."""

class Concordance:
    """Tranform synonym values for different naming and abbreviations used in different data sources.

    Examples: The New York Mets are sometimes abbreviated  NYM, sometimes NYN; K and SO are both strikeouts.

    Parameters
    ----------
    syn_set:
        A dictionary. Typcially, the keys will be possible variations on a name and values 
        will be the standard values that should be used in their place.
    standard_names: Iterable (optional)
        This is a list of standard values that are expected from `normalize`. If standard_names
        is not None, every name in standard_names is added to syn_set and mapped to itself.
        (This allows the normalize method to raise errors when the names are not found without
        explicitly including standard names in syn_set.)
    preprocess: Callable (optional)
        A callable that operates on values to normalize. This processes those keys to make them fit 
        permatations that are not equivalent to a computer. E.g., lambda x: x.upper().remove('.') 
        might be useful to translate acronymns that are sometimes done with periods, sometimes lower
        case, etc.
    """
    def __init__(self, syn_set: dict, standard_names=None, preprocess=lambda x: x):
        self.syn_set = syn_set.copy()
        self.prepreocess = preprocess
        if standard_names is not None:
            self.standard_names = set(standard_names)
            standard_dict = {k: k for k in standard_names}
            self.syn_set.update(standard_dict)
        
    def normalize(self, value, raise_error: False, default=lambda x: x):
        """Transform value into it's standard name.
        
        Parameters
        ----------
        raise_error:
            Throw KeyError if value is not in syn_set. Else, defer to default parameter.
        default: 
            Callable. If value is not found in syn_set, calls the callable on the value.
            Default is lambda x: x and returns the value if no alternative is found."""
        value = self.preprocess(value)
        if raise_error:
            return self.syn_set[value]
        elif default is None:
            return value
        return self.syn_set.get(value, default(value))
