import argparse
import pathlib
import numpy as np
import tensorflow
import PIL.Image


class Model:
    def __init__(self, model_filepath):
        self.graph_def = tensorflow.compat.v1.GraphDef()
        self.graph_def.ParseFromString(model_filepath.read_bytes())

        input_names, self.output_names = self._get_graph_inout(self.graph_def)
        assert len(input_names) == 1
        self.input_name = input_names[0]
        self.input_shape = self._get_input_shape(self.graph_def, self.input_name)

    def predict(self, image_filepath):
        image = PIL.Image.open(image_filepath).resize(self.input_shape)
        input_array = np.array(image, dtype=np.float32)[np.newaxis, :, :, :]
        input_array = input_array[:, :, :, (2, 1, 0)]  # => BGR

        with tensorflow.compat.v1.Session() as sess:
            tensorflow.import_graph_def(self.graph_def, name='')
            out_tensors = [sess.graph.get_tensor_by_name(o + ':0') for o in self.output_names]
            outputs = sess.run(out_tensors, {self.input_name + ':0': input_array})

        return {name: outputs[i] for i, name in enumerate(self.output_names)}

    @staticmethod
    def _get_graph_inout(graph_def):
        input_names = []
        inputs_set = set()
        outputs_set = set()

        for node in graph_def.node:
            if node.op == 'Placeholder':
                input_names.append(node.name)

            for i in node.input:
                inputs_set.add(i.split(':')[0])
            outputs_set.add(node.name)

        output_names = list(outputs_set - inputs_set)
        return input_names, output_names

    @staticmethod
    def _get_input_shape(graph_def, input_name):
        for node in graph_def.node:
            if node.name == input_name:
                return [dim.size for dim in node.attr['shape'].shape.dim][1:3]


def print_outputs(outputs):
    outputs = list(outputs.values())[0]
    for index, score in enumerate(outputs[0]):
        print(f"Label: {index}, score: {score:.5f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_filepath', type=pathlib.Path)
    parser.add_argument('image_filepath', type=pathlib.Path)

    args = parser.parse_args()

    model = Model(args.model_filepath)
    outputs = model.predict(args.image_filepath)
    print_outputs(outputs)


if __name__ == '__main__':
    main()
