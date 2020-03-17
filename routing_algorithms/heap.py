# -*- coding: utf-8 -*-
# https://towardsdatascience.com/data-structure-heap-23d4c78a6962

def min_heapify(array, indices, i):
    left_child_index = 2 * i + 1
    right_child_index = 2 * i + 2
    max_index_value = len(array) - 1
    smallest_key_index = i

    if left_child_index <= max_index_value and array[i][0] > array[left_child_index][0]:
        smallest_key_index = left_child_index
    if right_child_index <= max_index_value and array[left_child_index][0] > array[right_child_index][0]:
        smallest_key_index = right_child_index
    if smallest_key_index != i:
        array[i], array[smallest_key_index] = array[smallest_key_index], array[i]
        indices[i], indices[smallest_key_index] = indices[smallest_key_index], indices[i] #added by me
        min_heapify(array, indices, smallest_key_index)

def build_min_heap(array, indices):
    for i in range(len(array)//2,-1,-1):
        min_heapify(array, indices, i)
