import training
import OBC.networks
import argparse
import torch.nn as nn
import data_loader as dl
import math
import OBC.ClassificationMetric
from torchvision.datasets import ImageFolder
import par_sets as ps
import Piggyback.networks as pbnet

task_list = ["OC", "PE", "SC"]
folders = {
    "PE": '/home/fabio/robot_challenge/linemod',
    "SC": '/home/fabio/robot_challenge/NYUlab/data/images',
    "OC": '/home/fabio/robot_challenge/rod/split1'
}
network_list = ["resnet", "piggyback"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Masked model for VDA challenge')
    # NAMING-PARAMETERS
    parser.add_argument('--folder', type=str, default=None,
                        help='Where to locate the imgs')
    parser.add_argument('--pretrained', type=str, default=None,
                        help='Whether to use a pretrained model.')
    parser.add_argument('--prefix', type=str, default='noName',
                        help='Where to store the checkpoints')
    parser.add_argument('--visdom', type=str, default="training",
                        help='Select the visdom environment.')
    # TRAINING PARAMETERS
    parser.add_argument('--lr', type=float, default=None,
                        help='The learning rate to apply into training')
    parser.add_argument('--decay', type=float, default=None,
                        help='The learning rate to apply into training')
    parser.add_argument('--bs', type=int, default=None,
                        help='The learning rate to apply into training')
    parser.add_argument('--step', type=int, default=None,
                        help='The learning rate to apply into training')
    parser.add_argument('--epochs', type=int, default=None,
                        help='How many epochs to use for training')
    parser.add_argument('--set', type=str, default="def",
                        help='The parameter set')
    # SETTING PARAMETERS
    parser.add_argument('--frozen', type=int, default=0,
                        help='Whether to use fine tuning (0 - DEF) or feature extractor (1).')
    parser.add_argument('--task', type=str, default='PE',
                        help='Which is the task to run')
    parser.add_argument('--network', type=str, default='resnet',
                        help='Which is the network to use')
    parser.add_argument('--old', type=int, default=0,
                        help="Old model")

    args = parser.parse_args()
    
    TEST = 0
    task = args.task
    if task not in task_list:
        raise(Exception("Please be sure to use available task"))
        
    folder = args.folder if args.folder else folders[task]
    
    par_set = ps.get_parameter_set(args.set)
    step = args.step if args.step else par_set["step"]
    batch = args.bs if args.bs else par_set["batch"]
    epochs = args.epochs if args.epochs else par_set["epochs"]
    lr = args.lr if args.lr else par_set["lr"]
    decay = args.decay if args.decay else par_set["decay"]
    
    if task == "OC":
        classes = 51
        cost_function = nn.CrossEntropyLoss()
        metric = OBC.ClassificationMetric.ClassificationMetric()
        # Image folder for train and val
        train_loader = dl.get_image_folder_loaders(folder + "/train", ImageFolder, "SM", batch)
        test_loader = dl.get_image_folder_loaders(folder + "/val", ImageFolder, "NO", batch)
        index = 0
    elif task == "PE":
        import PoseEstimation.PELoss as pel
        from PoseEstimation.LinemodDataset import LinemodDataset
        classes = 15 + 3
        cost_function = pel.PE3DLoss(classes - 3)
        metric = pel.PEMetric(classes - 3, math.radians(5))
        train_loader = dl.get_image_folder_loaders(folder + "/train", LinemodDataset, "NO", batch)
        test_loader = dl.get_image_folder_loaders(folder + "/val", LinemodDataset, "NO", batch)
        index = 1
    elif task == "SC":
        classes = 10
        cost_function = nn.CrossEntropyLoss()
        metric = OBC.ClassificationMetric.ClassificationMetric()
        # Image folder for train and val
        train_loader = dl.get_image_folder_loaders(folder + "/train", ImageFolder, "SM", batch)
        test_loader = dl.get_image_folder_loaders(folder + "/val", ImageFolder, "NO", batch)
        index = 2
    else:
        # never executed, needed only for remove warnings.
        raise(Exception("Error in parameters. Task should be one between " + str(task_list)))
    
    # basic network (will be changed according to te baseline)
    if args.network == network_list[0]:
        model = OBC.networks.resnet18(classes, args.pretrained)
    elif args.network == network_list[1]:
        model = pbnet.piggyback_net([51, 18, 10], args.pretrained, args.old)
        model.set_index(index)
    else:
        raise(Exception("Error in parameters. Network should be one between " + str(network_list)))
    
    accuracy = 0
    if not TEST:
        accuracy = training.train(model, train_loader, test_loader, prefix=args.prefix, visdom_env=args.visdom,
                                  step=step, batch=batch, epochs=epochs, lr=lr, decay=decay,
                                  freeze=args.frozen, cost_function=cost_function, metric=metric)
    else:
        accuracy = training.test(model, test_loader, cost_function, metric)

    print("Final accuracy = " + str(accuracy))
