# Fortune Summoners Un/Packer v2.0.0

###### New and improved version!

Fortune Summoners Un/Packer is a command-line tool, written in Python 3, for handling graphic resources from the game Fortune Summoners: Secret of the Elemental Stone (henceforward referred to as FS or SotES).

The original project was started by rr-. I love this game, so I started working on my own version of this project as well.

There was nothing wrong with the old versions of this project, but motivated by recent interests from others I sought to re-work this into a much more friendly and robust tool (also I just tend to go way overboard if left alone, I am completely exhausted by the end of this).

## Features

I went all out! I added many new features that mostly (but not all!) try to make it as easy to use as possible for non-code-savvy users too:

* Packing support - bitmap images can be packed into SotES's image resource format. Yes, it works for what you're thinking of.
* Sprites are unpacked into their untouched Bitmap format, instead of PNGs. Turns out the original palettes are pretty important too.
* Unpacking is accurate, without guessing for metadata (though it was really cool how that was done).
* Now working as a complete command-line interface (it has colored output).
* Interactive mode for the CLI allows script to be run without parameters on Windows, featuring native dialogs to select files.

This is designed exclusively for FS english version 1.2, published on Steam. However, I have seen it work on other versions too.

## Requirements

* Python, verified on version 3.10+, but should work on some previous versions too.
* PIL Image library for packing.
* The sprite binary resource files must be previously extracted from SotES in order to be passed to the Un/packer.

## Usage

### Obtaining the binary resource files for sprites.
My recommendation for this task is `ResourceHacker`, however the original author's `Arc Unpacker` also works if you know how to use it.

For those using Resource Hacker:

   1. Pick `File > Open`, navigate to the game's folder and select `sotesd.dll`.
   2. On the left you should see some folders. Select the `DATA` folder.
   3. On the menu bar on the top, choose `Action > Save [ DATA ] group to an RC file ...` (make sure you pick **RC**).
   4. Save this to an empty folder of your choice. It will also save a `DATA.rc` file which is not necessary so you may delete it if you want.
   
Out of the binary files obtained, IDs 1180, 1986 and 2014 are not sprite resource files. You can delete them, or just pass them to the Unpacker and they will fail to be parsed.

`sotes.exe` also contains a few sprites, namely IDs 1392 through 1399, 1404 and 1451. You can also extract those and pass them to the Un/packer as well.

### Using the Unpacker

By now you should have the 756 or 766 (if you also extracted the ones from `sotes.exe`) sprite resources extracted, and be ready to use the Un/Packer.

There are multiple ways to run this program, but the recommended way is through the `run.bat` file. 

Double-click it to start the program, and the script will automatically try to run with the best python version available.

If no python version can be found (the console windows pops up but closes instantly) or if you want to run using a specific python version you have, you can open the `run.bat` file in a text editor and paste the location of your `python.exe` of choice into the `pythonpath` field (preferably between two double quotes like this: `pythonpath="C:/Path/to/my/python.exe"`).

You will then be asked what you wish to do, and provide the files you want to process, and a directory to save them in.

## Thanks

If you run into any issues at all, please report them to me through whichever is the best means you have. The program should fail sometimes, but never crash. Please don't be concerned with making duplicate threads or whatever, I appreciate all messages that will help my program be better.

Once again, thanks for rr- for starting the original project.

And visit our fan-made [Fortune Summoners Discord](https://discord.gg/N68c7pt)!
