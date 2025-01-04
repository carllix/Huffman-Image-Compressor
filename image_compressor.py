import numpy as np
from PIL import Image
import json
from collections import defaultdict
import heapq

class HuffmanNode:
    def __init__(self, value=None, freq=0):
        self.value = value
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


class ImageCompressor:
    def __init__(self):
        self.huffman_codes = {}
        self.huffman_tree = None

    def read_image(self, image_path):
        img = Image.open(image_path).convert("L")
        pixel_array = np.array(img).flatten()
        return pixel_array, img.size

    def calculate_frequencies(self, pixel_array):
        frequencies = defaultdict(int)
        for pixel in pixel_array:
            frequencies[pixel] += 1
        return frequencies

    def build_huffman_tree(self, frequencies):
        heap = []
        for value, freq in frequencies.items():
            node = HuffmanNode(value, freq)
            heapq.heappush(heap, node)

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)

            internal_node = HuffmanNode(freq=left.freq + right.freq)
            internal_node.left = left
            internal_node.right = right

            heapq.heappush(heap, internal_node)

        self.huffman_tree = heap[0]

    def generate_huffman_codes(self, node=None, code=""):
        if node is None:
            node = self.huffman_tree

        if node.value is not None:
            self.huffman_codes[node.value] = code
            return

        self.generate_huffman_codes(node.left, code + "0")
        self.generate_huffman_codes(node.right, code + "1")

    def encode_image(self, pixel_array):
        encoded_data = ""
        for pixel in pixel_array:
            encoded_data += self.huffman_codes[pixel]
        return encoded_data

    def save_compressed(self, encoded_data, codes, output_path):
        padded_length = 8 - (len(encoded_data) % 8)
        encoded_data += "0" * padded_length

        byte_array = bytearray()
        for i in range(0, len(encoded_data), 8):
            byte = encoded_data[i:i+8]
            byte_array.append(int(byte, 2))

        with open(output_path + ".bin", "wb") as f:
            f.write(bytes([padded_length]))
            f.write(byte_array)

        with open(output_path + "_codes.json", "w") as f:
            json.dump({str(k): v for k, v in codes.items()}, f)

    def calculate_compression_ratio(self, original_size, compressed_size):
        return compressed_size/original_size * 100

    def decode_image(self, input_path, codes_path, output_path, original_size):
        with open(codes_path, 'r') as f:
            codes = json.load(f)
            codes = {int(k): v for k, v in codes.items()}

        with open(input_path, 'rb') as f:
            padding_length = int.from_bytes(f.read(1), byteorder='big')
            byte_data = f.read()

        binary_data = ""
        for byte in byte_data:
            binary_data += format(byte, '08b')
        binary_data = binary_data[:-padding_length] if padding_length > 0 else binary_data

        reverse_codes = {v: k for k, v in codes.items()}
        current_code = ""
        decoded_pixels = []

        for bit in binary_data:
            current_code += bit
            if current_code in reverse_codes:
                decoded_pixels.append(reverse_codes[current_code])
                current_code = ""

        decoded_array = np.array(decoded_pixels, dtype=np.uint8)
        decoded_image = Image.fromarray(decoded_array.reshape(original_size[::-1]))
        decoded_image.save(output_path)

    def compress(self, input_path, output_path):
        pixel_array, original_size = self.read_image(input_path)
        frequencies = self.calculate_frequencies(pixel_array)

        self.build_huffman_tree(frequencies)
        self.generate_huffman_codes()

        encoded_data = self.encode_image(pixel_array)
        self.save_compressed(encoded_data, self.huffman_codes, output_path)

        original_bits = len(pixel_array) * 8
        compressed_bits = len(encoded_data)
        compression_ratio = self.calculate_compression_ratio(
            original_bits, compressed_bits
        )

        return {
            "original_size": original_size,
            "compression_ratio": compression_ratio,
            "original_bits": original_bits,
            "compressed_bits": compressed_bits,
        }
