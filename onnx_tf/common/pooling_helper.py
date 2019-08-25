import numpy as np
import itertools
import math


def calc_pads_same(in_spatial_shape, kernel_shape, strides,
                   dilations, padding):
    pads_begin = []
    pads_end = []
    spatial_size = len(in_spatial_shape)
    for i in range(spatial_size):
        in_size = in_spatial_shape[i]
        filter_size = (kernel_shape[i] - 1) * dilations[i] + 1

        out_size = int(math.ceil(in_size / strides[i]))
        pad_along_axis = max((out_size - 1) * strides[i] +
                             filter_size - in_size, 0)
        if padding.lower() == "same_lower":
            pad_op = math.ceil
        else:
            pad_op = math.floor
        pad_begin = int(pad_op(pad_along_axis / 2))
        pad_end = pad_along_axis - pad_begin

        pads_begin.append(pad_begin)
        pads_end.append(pad_end)

    return pads_begin + pads_end


def py_maxpool(input, kernel_shape, strides=None, dilations=None,
               padding=None, ceil_mode=False):
    """
        Implementation of MaxPool operation in Python
        Args:
            input:        input N-D data array in NC* format
            kernel_shape: the size of the kernel along each axis
            strides:      stride along each spatial axis
            dilations:    dilations value along each spatial axis of filter
            padding:      padding for the beginning and ending along each
                          spatial axis. `padding` format should be as follow
                          [x1_begin, x2_begin...x1_end, x2_end,...]
            ceil_mode:    whether to use ceil or floor (default) to compute
                          the output shape.
      Return:
            pooled:       output data from max pooling across the input
            ind:          indices of the selected max values from the input
    """

    def _pooling_output_shape(input_size, ksize, stride,
                              dilation, pad, ceil_mode):
        output_size = (input_size + pad - ((ksize - 1) * dilation + 1) +
                       ((stride-1) if ceil_mode else 0)) // stride + 1
        if (pad):
            if ((output_size - 1) * stride >= input_size + pad):
                output_size -= 1
        return output_size

    def _loop_over_output(batch, channel):
        dims = [range(output_sp_shape[d]) for d in range(spatial_size)]
        for counters in itertools.product(*dims):
            input_ranges = []
            for dim in range(spatial_size):
                dim_start = \
                    counters[dim] * strides[dim] - pads[dim * 2]
                dim_end = \
                    min(dim_start + (kernel_shape[dim] - 1) * dilations[dim]
                        + 1, inp_sp_shape[dim])
                while dim_start < 0:
                    dim_start += dilations[dim]

                cur_range = [i for i in range(dim_start,
                                              dim_end, dilations[dim])]
                input_ranges.append(cur_range)
            maxval = -inf
            maxind = -1
            for input_ind in itertools.product(*input_ranges):
                ind = (batch, channel) + input_ind
                val = input[ind]
                if val > maxval:
                    maxval = val
                    ind = 0
                    for i in range(spatial_size):
                        coef = 1
                        for j in range(i+1, spatial_size):
                            coef *= inp_sp_shape[j]
                        ind += input_ind[i] * coef
                    maxind = ind
            ind = (batch, channel) + counters
            out_pool[ind] = maxval
            out_ind[ind] = maxind

    spatial_size = len(kernel_shape)

    input_shape = np.shape(input)
    iheight, iwidth = input_shape[2:4]

    oheight = _pooling_output_shape(iheight, kH, sH, dH, padH, ceil_mode)
    owidth = _pooling_output_shape(iwidth, kW, sW, dW, padW, ceil_mode)

    out_pool = np.zeros((input_shape[0], input_shape[1],
                        oheight, owidth), input.dtype)
    out_ind = np.zeros((input_shape[0], input_shape[1],
                       oheight, owidth), 'int64')

    for batch in range(input_shape[0]):
        for channel in range(input_shape[1]):
            # Loop over output
            for i in range(oheight):
                for j in range(owidth):
                    hstart = i * sH - pad_top
                    wstart = j * sW - pad_left
                    hend = min(hstart + (kH - 1) * dH + 1, iheight)
                    wend = min(wstart + (kW - 1) * dW + 1, iwidth)
                    while hstart < 0:
                        hstart += dH
                    while wstart < 0:
                        wstart += dW

                    maxind = -1
                    maxval = -np.inf

                    for y in range(hstart, hend, dH):
                        for x in range(wstart, wend, dW):
                            val = input[batch][channel][y][x]
                            if val > maxval:
                                maxval = val
                                maxind = y * iwidth + x
                    out_pool[batch][channel][i][j] = maxval
                    out_ind[batch][channel][i][j] = maxind

    return (out_pool, out_ind)
