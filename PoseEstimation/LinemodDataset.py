from torch.utils.data import Dataset
import torch
import numpy as np
import sys
import os
from PIL import Image
from PoseEstimation.utils import quaternion_from_matrix


def linemod_rotation(fname):
    """
    read a 3x3 rotation and trasform it into quaternion
    """
    R = open(fname)
    R.readline()  # discard first line
    R = np.float32(R.read().split()).reshape(3, 3)  # save the matrix
    
    q = quaternion_from_matrix(R)
    
    return q


def make_dataset(dir, class_to_idx):
    images = []
    dir = os.path.expanduser(dir)
    for target in sorted(class_to_idx.keys()):
        d = os.path.join(dir, target)
        if not os.path.isdir(d):
            continue
        index = 0
        for fname in os.listdir(d):
            if "jpg" in fname:
                path_rot = os.path.join(d, fname[:-3] + "rot")
                quaternion = linemod_rotation(path_rot)
                t = [class_to_idx[target]] + quaternion.tolist()
                # print(quaternion, end='\t')
                t = torch.FloatTensor(t)
                # print(t)
                path = os.path.join(d, fname[:-3] + "jpg")
                item = (path, t)
                images.append(item)

    return images


def pil_loader(path):
    # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
    with open(path, 'rb') as f:
        img = Image.open(f)
        return img.convert('RGB')


class LinemodDataset(Dataset):
    """ Linemod dataset."""
    
    def __init__(self, root, transform=None, target_transform=None):
    
        classes, class_to_idx = self._find_classes(root)
        samples = make_dataset(root, class_to_idx)
        if len(samples) == 0:
            raise (RuntimeError("Found 0 files in subfolder of " + root + "\n"))
        
        self.loader = pil_loader
        self.root = root
        self.transform = transform
        self.classes = classes
        self.class_to_idx = class_to_idx
        self.samples = samples
        self.targets = [s[1] for s in samples]
        self.target_transform = target_transform
        
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, index):
        """
        Args:
            index (int): Index
        Returns:
            tuple: (sample, target) where:
                target is class_index of the target class plus the associated quaternion
                
        """
        path, target = self.samples[index]
        sample = self.loader(path)
        if self.transform is not None:
            sample = self.transform(sample)
        if self.target_transform is not None:
            target = self.target_transform(target)
    
        return sample, target

    def _find_classes(self, dir):
        """
        Finds the class folders in a dataset.
        Args:
            dir (string): Root directory path.
        Returns:
            tuple: (classes, class_to_idx) where classes are relative to (dir), and class_to_idx is a dictionary.
        Ensures:
            No class is a subdirectory of another.
        """
        if sys.version_info >= (3, 5):
            # Faster and available in Python 3.5 and above
            classes = [d.name for d in os.scandir(dir) if d.is_dir()]
        else:
            classes = [d for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
        classes.sort()
        class_to_idx = {classes[i]: i for i in range(len(classes))}
        return classes, class_to_idx

    def __repr__(self):
        fmt_str = 'Dataset ' + self.__class__.__name__ + '\n'
        fmt_str += '    Number of datapoints: {}\n'.format(self.__len__())
        fmt_str += '    Root Location: {}\n'.format(self.root)
        tmp = '    Transforms (if any): '
        fmt_str += '{0}{1}\n'.format(tmp, self.transform.__repr__().replace('\n', '\n' + ' ' * len(tmp)))
        tmp = '    Target Transforms (if any): '
        fmt_str += '{0}{1}'.format(tmp, self.target_transform.__repr__().replace('\n', '\n' + ' ' * len(tmp)))
        return fmt_str