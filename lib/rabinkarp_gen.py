import pybindgen


def generate(file_):
    mod = pybindgen.Module('_rabinkarprh')
    mod.add_include('"rabinkarp.h"')
    mod.add_container('std::list<unsigned int>', 'unsigned int', 'list')
    mod.add_container('std::list<double>', 'double', 'list')

    cls = mod.add_class('RabinKarpHash')
    cls.add_constructor([pybindgen.param('int', 'my_window_size'),
                         pybindgen.param('int', 'seed')])
    cls.add_method('set_threshold',
                   None,
                   [pybindgen.param('double', 'my_threshold')])
    cls.add_method('next_chunk_boundaries',
                   pybindgen.retval('std::list<unsigned int>'),
                   [pybindgen.param('std::string*', 'str'),
                    pybindgen.param('unsigned int', 'prepend_bytes')])

    cls = mod.add_class('RabinKarpMultiThresholdHash')
    cls.add_constructor([pybindgen.param('int', 'my_window_size'),
                         pybindgen.param('int', 'seed'),
                         pybindgen.param('std::list<double>', 'my_thresholds')])
    cls.add_method('next_chunk_boundaries_with_thresholds',
                   pybindgen.retval('std::list<unsigned int>'),
                   [pybindgen.param('std::string*', 'str'),
                    pybindgen.param('unsigned int', 'prepend_bytes')])

    mod.generate(file_)
