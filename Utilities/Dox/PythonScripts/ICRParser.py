import ICRFileToJson
import ICRJsonToHtml

import argparse
import os

from LogManager import initConsoleLogging

def run(args):
    filename = os.path.basename(args.icrfile)[:-4] # Remove '.txt'
    args.icrJsonFile = os.path.join(args.outdir, filename + ".JSON")

    ICRFileToJson.run(args)

    args.date = ICRFileToJson.date
    if args.date is None:
        # No date specified in the file, try to parse the filename
        # Expected format: <month>_<day>_<year>_IA_Listing_Descriptions.TXT
        filename = args.icrfile
        s = filename.find("_IA_Listing_Descriptions")
        if s > 0:
            date_str = filename[:s]
            vals = date_str.split("_")
            if len(vals) == 3:
                args.date = vals[0] + " " + vals[1] + "," + vals[2]

    if args.html:
      ICRJsonToHtml.run(args)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='VistA ICR Parser')
    parser.add_argument('-mr', '--MRepositDir', required=True,
                          help='VistA M Component Git Repository Directory')
    parser.add_argument('-pr', '--patchRepositDir', required=True,
                          help="VistA Git Repository Directory")
    parser.add_argument('icrfile', help='path to the VistA ICR file')
    parser.add_argument('outdir', help='path to the output web page directory')
    parser.add_argument('-html', action='store_true',
                          help='generate html')
    result = parser.parse_args()
    initConsoleLogging()
    run(result)
