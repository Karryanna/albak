#!/usr/bin/env python3

import argparse
import datetime
import exifread
import subprocess
import sys

from pathlib import Path

DESIRED_LONGER = 2126
DESIRED_SHORTER = 1535

RESIZE_TAGS_NEEDED = ['EXIF ExifImageWidth', 'EXIF ExifImageLength']

argparser = argparse.ArgumentParser()
argparser.add_argument('--base-dir', default='source')
argparser.add_argument('--dest-dir', default='processed')
argparser.add_argument('--rename', action='store_true')
argparser.add_argument('--name-mask')
argparser.add_argument('--no-resize', dest='resize', action='store_false')
args = argparser.parse_args()

counts = {}

dirs = [args.base_dir]

for dir in dirs:
  p = Path(dir)
  if not p.is_dir():
    print('{} is not directory'.format(p), format=sys.stderr)
    continue

  for f in p.iterdir():
    if f.is_dir():
      dirs.append(f)
      continue

    elif f.is_file():
      if not f.suffix.lower()[1:] in ['jpg', 'jpeg', 'png']:
        print('Skipping file {}'.format(f), file=sys.stderr)
        continue

    with open(f, 'rb') as imagefile:
      tags = exifread.process_file(imagefile)

    stop_iteration = False

    resize_size = '100%'
    if args.resize:
      for t in RESIZE_TAGS_NEEDED:
        if not t in tags:
          print('Cannot find required tag {} in {}'.format(t, f), file=sys.stderr)
          stop_iteration = True
      if stop_iteration:
        continue

      img_width = int(str(tags['EXIF ExifImageWidth']))
      img_height = int(str(tags['EXIF ExifImageLength']))

      if (img_width > DESIRED_LONGER and img_height > DESIRED_SHORTER) or \
         (img_width > DESIRED_SHORTER and img_height > DESIRED_LONGER):
        if img_width > img_height:
          perc = DESIRED_LONGER / img_width
          resize_size = '{}x{}'.format(DESIRED_LONGER, int(img_height * perc))
        else:
          perc = DESIRED_LONGER / img_height
          resize_size = '{}x{}'.format(int(img_width * perc), DESIRED_LONGER)

    new_name = f.name
    if args.rename:
      if args.name_mask:
        new_name = args.name_mask
      else:
        if 'EXIF DateTimeOriginal' not in tags:
          print('Cannot find required tag DateTimeOriginal in {}'.format(f), file=sys.stderr)
          continue
        exifdate = tags['EXIF DateTimeOriginal']
        if str(exifdate).startswith('0000'):
          print('Value of DateTimeOriginal tag ({}) does not make sense in {}'.format(exifdate, f), file=sys.stderr)
          continue
        dt = datetime.datetime.strptime(str(exifdate), '%Y:%m:%d %H:%M:%S')
        new_name = datetime.datetime.strftime(dt, '%Y-%m-%d %H.%M.%S')

        if new_name in counts:
          counts[new_name] += 1
          new_name += '-' + str(counts[new_name])
        else:
          counts[new_name] = 1
        new_name += '.jpg'
        print('{} => {}'.format(str(f), new_name))

    subprocess.run(['convert', '-resize', resize_size, f, args.dest_dir + '/' + new_name])
