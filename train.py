# -*- coding: utf-8 -*-
"""
@author: Niklas Bretschneider
@title: training file for Image Classifier Project on Udacity
"""
# ------------------------------------------------------------------------------- #
# This imports the required libraries
# ------------------------------------------------------------------------------- #

# Import torch and argparse
import torch
import argparse

# Import OrderedDict and IsDir
from collections import OrderedDict
from os.path import isdir

# Import nn and optim from torch, as well as some packages from torchvision
from torch import nn
from torch import optim
from torchvision import datasets, transforms, models

# ------------------------------------------------------------------------------- #
# This defines the functions we need for training
# ------------------------------------------------------------------------------- #
# *REVISED* Function arg_parser() parses keyword arguments from the command line


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


# Function train_transformer(train_dir) performs training transformations on a dataset
def train_transformer(train_dir):
    # Define transformation
    train_transforms = transforms.Compose([transforms.RandomRotation(30),
                                       transforms.RandomResizedCrop(224),
                                       transforms.RandomHorizontalFlip(),
                                       transforms.ToTensor(),
                                       transforms.Normalize([0.485, 0.456, 0.406],
                                                            [0.229, 0.224, 0.225])])

    # Load the Data
    train_data = datasets.ImageFolder(train_dir, transform=train_transforms)
    return train_data



# Function test_transformer(test_dir) performs test/validation transformations on a dataset
def test_transformer(test_dir):
    # Define transformation
    test_transforms = transforms.Compose([transforms.Resize(256),
                                      transforms.CenterCrop(224),
                                      transforms.ToTensor(),
                                      transforms.Normalize([0.485, 0.456, 0.406],
                                                           [0.229, 0.224, 0.225])])
    # Load the Data
    test_data = datasets.ImageFolder(test_dir, transform=test_transforms)
    return test_data



# Function data_loader(data, train=True) creates a dataloader from dataset imported
def data_loader(data, train=True):
    if train:
        loader = torch.utils.data.DataLoader(data, batch_size=50, shuffle=True)
    else:
        loader = torch.utils.data.DataLoader(data, batch_size=50)
    return loader



# Function check_gpu(gpu_arg) make decision on using CUDA with GPU or CPU
def check_gpu(gpu_arg):
   # If gpu_arg is false then simply return the cpu device
    if not gpu_arg:
        return torch.device("cpu")


    # If gpu_arg then make sure to check for CUDA before assigning it
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


    # Print result
    if device == "cpu":
        print("CUDA was not found on device, using CPU instead.")
    return device



# primaryloader_model(architecture="vgg16") downloads model (primary) from torchvision
def primaryloader_model(architecture="vgg16"):
    # Load Defaults if none specified
    if type(architecture) == type(None):
        model = models.vgg16(pretrained=True)
        model.name = "vgg16"
        print("Network architecture specified as vgg16.")
    else:
        exec("model = models.{}(pretrained=True)".format(architecture))
        model.name = architecture


    # Freeze parameters so we don't backprop through them
    for param in model.parameters():
        param.requires_grad = False
    return model


# Function initial_classifier(model, hidden_units) creates a classifier with the corect number of input layers
def initial_classifier(model, hidden_units):
    # Check that hidden layers has been input
    if type(hidden_units) == type(None):
        hidden_units = 4096 #hyperparamters
        print("Number of Hidden Layers specificed as 4096.")


    # Find Input Layers
    input_features = model.classifier[0].in_features


    # Define Classifier
    classifier = nn.Sequential(OrderedDict([
                          ('fc1', nn.Linear(input_features, hidden_units, bias=True)),
                          ('relu1', nn.ReLU()),
                          ('dropout1', nn.Dropout(p=0.5)),
                          ('fc2', nn.Linear(hidden_units, 102, bias=True)),
                          ('output', nn.LogSoftmax(dim=1))
                          ]))
    # Return the classifier
    return classifier


# Function validation(model, testloader, criterion, device) validates training against testloader to return loss and accuracy
def validation(model, testloader, criterion, device):
    test_loss = 0
    accuracy = 0


    for ii, (inputs, labels) in enumerate(testloader):


        inputs, labels = inputs.to(device), labels.to(device)


        output = model.forward(inputs)
        test_loss += criterion(output, labels).item()


        ps = torch.exp(output)
        equality = (labels.data == ps.max(dim=1)[1])
        accuracy += equality.type(torch.FloatTensor).mean()
    return test_loss, accuracy


# Function network_trainer represents the training of the network model
def network_trainer(Model, Trainloader, Testloader, Device,
                  Criterion, Optimizer, Epochs, Print_every, Steps):

    # Check Model Kwarg
    if type(Epochs) == type(None):
        Epochs = 5
        print("Number of Epochs specificed as 5.")

    # Prints out initializiation message
    print("Training process initializing .....\n")


    # Train Model
    for e in range(Epochs):
        running_loss = 0
        Model.train() # Technically not necessary, setting this for good measure


        for ii, (inputs, labels) in enumerate(Trainloader):
            Steps += 1


            inputs, labels = inputs.to(Device), labels.to(Device)


            Optimizer.zero_grad()


            # Forward and backward passes
            outputs = model.forward(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            # This increments running_loss
            running_loss += loss.item()


            if steps % print_every == 0:
                model.eval()


                with torch.no_grad():
                    valid_loss, accuracy = validation(model, validloader, criterion)


                print("Epoch: {}/{} | ".format(e+1, epochs),
                     "Training Loss: {:.4f} | ".format(running_loss/print_every),
                     "Validation Loss: {:.4f} | ".format(valid_loss/len(testloader)),
                     "Validation Accuracy: {:.4f}".format(accuracy/len(testloader)))


                running_loss = 0
                model.train()

    # This returens the model
    return Model

#Function validate_model(Model, Testloader, Device) validate the above model on test data images
def validate_model(Model, Testloader, Device):

   # Do validation on the test set
    correct = 0
    total = 0
    with torch.no_grad():
        Model.eval()
        for data in Testloader:
            images, labels = data
            images, labels = images.to(Device), labels.to(Device)
            outputs = Model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    # This prints out the achieved accuracy
    print('Accuracy achieved by the network on test images is: %d%%' % (100 * correct / total))


# Function initial_checkpoint(Model, Save_Dir, Train_data) saves the model at a defined checkpoint
def initial_checkpoint(Model, Save_Dir, Train_data):


    # Save model at checkpoint
    if type(Save_Dir) == type(None):
        print("Model checkpoint directory not specified, model will not be saved.")
    else:
        if isdir(Save_Dir):
            # Create `class_to_idx` attribute in model
            Model.class_to_idx = Train_data.class_to_idx


            # Create checkpoint dictionary
            checkpoint = {'architecture': Model.name,
                          'class_to_idx': Model.class_to_idx,
                          'state_dict': Model.state_dict()}

            # Check for ResNet vs Others
            if Model.name == "resnet101":
                checkpoint["fc"] = Model.fc
            else:
                checkpoint["classifier"] = Model.classifier

            # Save checkpoint
            torch.save(checkpoint, 'my_checkpoint.pth')


        else:
            print("Directory not found, model will not be saved.")


# =============================================================================
# This defines the main function
# =============================================================================

# Function main() is where all the above functions are called and executed
def main():


    # Get Keyword Args for Training
    args = arg_parser()


    # Set directory for training
    data_dir = 'flowers'
    train_dir = data_dir + '/train'
    valid_dir = data_dir + '/valid'
    test_dir = data_dir + '/test'


    # Pass transforms in, then create trainloader
    train_data = test_transformer(train_dir)
    valid_data = train_transformer(valid_dir)
    test_data = train_transformer(test_dir)


    trainloader = data_loader(train_data)
    validloader = data_loader(valid_data, train=False)
    testloader = data_loader(test_data, train=False)


    # Load Model
    model = primaryloader_model(architecture=args.arch)


    # Build Classifier
    model.classifier = initial_classifier(model,
                                         hidden_units=args.hidden_units)


    # Check for GPU
    device = check_gpu(gpu_arg=args.gpu);


    # Send model to device
    model.to(device);



    # Define loss and optimizer
    criterion = nn.NLLLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=learning_rate)


    # Define deep learning method
    print_every = 30
    steps = 0



    # Train the classifier layers using backpropogation
    trained_model = network_trainer(model, trainloader, validloader,
                                  device, criterion, optimizer, args.epochs,
                                  print_every, steps)

    # Prints out the successful training message
    print("\nThe training process is now complete!")

    # This validates the model
    validate_model(trained_model, testloader, device)

    # This saves the model
    initial_checkpoint(trained_model, args.save_dir, train_data)


# =============================================================================
# This runs the program
# =============================================================================
if __name__ == '__main__': main()
