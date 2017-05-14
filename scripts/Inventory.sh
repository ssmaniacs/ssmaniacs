#!/bin/bash
{
  python ItemInfo.py . json en element
  python ItemInfo.py . json en inventory banish special
} | sed -nE '/^[0-9]/s/(.+)\t(.+)\t(.+)\t(.+)\t(.+)/\1,\4,\3/p' 
