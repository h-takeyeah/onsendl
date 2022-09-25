# OnsenDL

audio download tool for [onsen](https://www.onsen.ag) listener

## :wrench: Try

```plain
git clone https://github.com/h-takeyeah/onsendl.git
cd onsendl
# install dependencies
pipenv install
pipenv shell
# run
python -m onsendl https://www.onsen.ag/program/<title>
```

- **ffmpeg** is required
- pipx integration and global install is not tested.

## :runner: Usage

1. Go to [onsen.ag](onsen.ag)
2. Search favorite program and click *to program site*
  ![usage1](./asset/usage1.png)
3. Copy URL of the opened tab
  ![usage2](./asset/usage2.png)
4. Pass URL to onsendl
5. All episodes will be downloaded to current directory

```plain
usage: __main__.py [-h] program_url

positional arguments:
  program_url  url of onsen.ag radio program

options:
  -h, --help   show this help message and exit
```

## :dart: TODO

- sequential play without downloading
- build

## Escape clause

I can't take responsibility or liability for any consequences resulting from use of this software.
