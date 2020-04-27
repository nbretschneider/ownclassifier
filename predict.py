# -*- coding: utf-8 -*-
"""
@author: Niklas Bretschneider
@title: prediction file for Image Classifier Project on Udacity
"""


# ------------------------------------------------------------------------------- #
# This imports the required libraries
# ------------------------------------------------------------------------------- #

## Import json and argparse
import json
import argparse

## Import torch, numpy and PIL
import torch
import numpy as np
import PIL

## Import train, math and torchvision
from train import check_gpu
from math import ceil
from torchvision import models


# ------------------------------------------------------------------------------- #
# This defines the functions, i.e. arg_parser, load_checkpoint,
# process_image, predict, and print_probability
# ------------------------------------------------------------------------------- #


# This function arg_parser() parses keyword arguments from the command line
def arg_parser():
    parser = argparse.ArgumentParser()

    # Data-dir
    parser.add_argument('data_dir', type=str, help='Directory to training images')

    # Save-dir
    parser.add_argument('--save_dir', type=str, default='checkpoints', help='Directory to save checkpoints')

    # Arch
    parser.add_argument('--arch', dest='arch', default='densenet161', action='store',choices=['vgg13', 'densenet161'], help='Architecture')

    # Learning-rate
    parser.add_argument('--learning_rate', type=float, default=0.01, help='Learning rate')

    # Hidden_units
    parser.add_argument('--hidden_units', type=int, default=512, help='hidden units')

    # Epochs
    parser.add_argument('--epochs', type=int, default=20, help='Epoch count')

    # GPU
    parser.add_argument('--gpu', dest='gpu', action='store_true', help='Use GPU for training')

    # Set-defaults
    parser.set_defaults(gpu=False)

    # Returns parser.parse_args
    return parser.parse_args()



# This function load_checkpoint(checkpoint_path) loads our saved deep learning model from checkpoint
def load_checkpoint(checkpoint_path):
    # Load the saved file
    checkpoint = torch.load("my_checkpoint.pth")


    # Load Defaults if none specified
    if checkpoint['architecture'] == 'vgg16':
        model = models.vgg16(pretrained=True)
        model.name = "vgg16"
    else:
        exec("model = models.{}(pretrained=True)".checkpoint['architecture'])
        model.name = checkpoint['architecture']


    # Freeze parameters so we don't backprop through them
    for param in model.parameters(): param.requires_grad = False


    # Load stuff from checkpoint
    model.class_to_idx = checkpoint['class_to_idx']
    model.classifier = checkpoint['classifier']
    model.load_state_dict(checkpoint['state_dict'])

    # Return model
    return model


# Function process_image(image_path) performs cropping, scaling of image for our model
def process_image(image_path):
    test_image = PIL.Image.open(image_path)


    # Get original dimensions
    orig_width, orig_height = test_image.size


    # Find shorter size and create settings to crop shortest side to 256
    if orig_width < orig_height: resize_size=[256, 256**600]
    else: resize_size=[256**600, 256]

    # Resize the test_image
    test_image.thumbnail(size=resize_size)


    # Find pixels to crop on to create 224x224 image
    center = orig_width/4, orig_height/4
    left, top, right, bottom = center[0]-(244/2), center[1]-(244/2), center[0]+(244/2), center[1]+(244/2)
    test_image = test_image.crop((left, top, right, bottom))


    # Converrt to numpy - 244x244 image w/ 3 channels (RGB)
    np_image = np.array(test_image)/255 # Divided by 255 because imshow() expects integers (0:1)!!


    # Normalize each color channel
    normalise_means = [0.485, 0.456, 0.406]
    normalise_std = [0.229, 0.224, 0.225]
    np_image = (np_image-normalise_means)/normalise_std


    # Set the color to the first channel
    np_image = np_image.transpose(2, 0, 1)

    # Return np_image
    return np_image


def predict(image_tensor, model, device, cat_to_name, top_k):
    ''' Predict the class (or classes) of an image using a trained deep learning model.

    image_path: string. Path to image, directly to image and not to folder.
    model: pytorch neural network.
    top_k: integer. The top K classes to be calculated

    returns top_probabilities(k), top_labels
    '''


    # check top_k
    if type(top_k) == type(None):
        top_k = 5
        print("Top K not specified, assuming K=5.")


    # Set model to evaluate
    model.eval();


    # Convert image from numpy to torch
    torch_image = torch.from_numpy(np.expand_dims(image_tensor,
                                                  axis=0)).type(torch.FloatTensor)


    model=model.cpu()


    # Find probabilities (results) by passing through the function (note the log softmax means that its on a log scale)
    log_probs = model.forward(torch_image)


    # Convert to linear scale
    linear_probs = torch.exp(log_probs)


    # Find the top 5 results
    top_probs, top_labels = linear_probs.topk(top_k)


    # Detatch all of the details
    top_probs = np.array(top_probs.detach())[0] # This is not the correct way to do it but the correct way isnt working thanks to cpu/gpu issues so I don't care.
    top_labels = np.array(top_labels.detach())[0]


    # Convert to classes
    idx_to_class = {val: key for key, val in
                                      model.class_to_idx.items()}
    top_labels = [idx_to_class[lab] for lab in top_labels]
    top_flowers = [cat_to_name[lab] for lab in top_labels]

    # Return top_probs, top_labels and top_flowers
    return top_probs, top_labels, top_flowers


def print_probability(probs, flowers):
    """
    Converts two lists into a dictionary to print on screen
    """


    for i, j in enumerate(zip(flowers, probs)):
        print ("Rank {}:".format(i+1),
               "Flower: {}, liklihood: {}%".format(j[1], ceil(j[0]*100)))


# =============================================================================
# Main Function
# =============================================================================


def main():
    """
    Executing relevant functions
    """


    # Get Keyword Args for Prediction
    args = arg_parser()


    # Load categories to names json file
    with open(args.category_names, 'r') as f:
        	cat_to_name = json.load(f)


    # Load model trained with train.py
    model = load_checkpoint(args.checkpoint)


    # Process Image
    image_tensor = process_image(args.image)


    # Check for GPU
    device = check_gpu(gpu_arg=args.gpu);


    # Use `processed_image` to predict the top K most likely classes
    top_probs, top_labels, top_flowers = predict(image_tensor, model,
                                                 device, cat_to_name,
                                                 args.top_k)


    # Print out probabilities
    print_probability(top_flowers, top_probs)

# =============================================================================
# This finally runs the programm using main()
# =============================================================================

if __name__ == '__main__': main()
