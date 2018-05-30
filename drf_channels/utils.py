def get_group_name(model_label, action, id=None):
    if id:
        return '{}-{}-{}'.format(model_label, action, id)
    else:
        return '{}-{}'.format(model_label, action)
