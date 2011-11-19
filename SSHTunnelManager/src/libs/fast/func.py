# -*- coding: utf-8 -*-


def method_exists(class_name, method_name):
    return hasattr(class_name, method_name) and callable(getattr(class_name, method_name))


