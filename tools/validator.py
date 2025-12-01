import jsonschema

schema = {
  'type': 'object',
  'properties': {
    'date': {'type': ['string', 'null']},
    'vendor': {'type': ['string', 'null']},
    'amount': {'type': ['number', 'null']},
    'currency': {'type': ['string', 'null']},
    'desc': {'type': ['string', 'null']},
    'source': {'type': 'string'}
  },
  'required': ['amount', 'source']
}

def validate(x):
    """ 
    Validate x against the predefined schema.
    """
    
    try:
        jsonschema.validate(instance=x, schema=schema)
        return True
    except Exception:
        return False
