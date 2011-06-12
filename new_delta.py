#   Copyright (C) 2011 Crystalnix <vgachkaylo@crystalnix.com>

#   This file is part of omaha-server.

#   omaha-server is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   omaha-server is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with omaha-server.  If not, see <http://www.gnu.org/licenses/>.

import re
from twisted.web import resource
from config import Config
from util import *
import hashlib, base64

class NewDeltaResource(resource.Resource):
    isLeaf = True
    pathFromRoot = '/service/admin/new_delta'

    def render_GET(self, request):
        output = """<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="chrome=1">

    <title>House of Life Update Manager</title>

    <!-- CSS: implied media="all" -->
    <link rel="stylesheet" href="/css/style.css?v=2">
    <link rel="stylesheet" href="/css/upload.css?v=2">

    <script type="text/javascript">
        uploadPath = "{0}";
    </script>
    <script type="text/javascript" src="/js/upload.js"></script>
</head>
<body>
    <div id="container">
        <header>
        </header>
        <div id="main" role="main">""".format(self.pathFromRoot)

        output += """
            <form id="form1" enctype="multipart/form-data" method="post" action="{0}">
              <div class="row">
                <label for="fromVersion">Input "From" Delta Update Version Number</label><br />
                <input type="text" name="fromVersion" id="fromVersion" />
              </div>
              <div class="row">
                <label for="fileToUpload">Select a File to Upload</label><br />
                <input type="file" name="fileToUpload" id="fileToUpload" onchange="fileSelected();"/>
              </div>
              <div class="row">
              <input type="button" onclick="uploadFile()" value="Upload" />
              </div>
              <div id="fileInfo">
                <div id="fileName"></div>
                <div id="fileSize"></div>
                <div id="fileType"></div>
              </div>
              <div class="row"></div>
              <div id="progressIndicator">
                <div id="progressBar" class="floatLeft">
                </div>
                <div id="progressNumber" class="floatRight">&nbsp;</div>
                <div class="clear"></div>
                <div>
                  <div id="transferSpeedInfo" class="floatLeft" style="width: 80px;">&nbsp;</div>
                  <div id="timeRemainingInfo" class="floatLeft" style="margin-left: 10px;">&nbsp;</div>
                  <div id="transferBytesInfo" class="floatRight" style="text-align: right;">&nbsp;</div>
                  <div class="clear"></div>
                </div>
                <div id="uploadResponse"></div>
              </div>
              <p>
                <a href="/service/admin">Back to main page</a>
              </p>
            </form>""".format(self.pathFromRoot)

        output += """
        </div>
        <footer>
        </footer>
    </div>
</body>
</html>"""
        return output

    def render_POST(self, request):
        """
        
        """
        versionRegex = re.compile('^\d+\.\d+\.\d+\.\d+$')
        if not versionRegex.match(request.args['fromVersion'][0]):
            request.setResponseCode(400) # Bad request
            return "Error: malformed version number."

        newDict = loadJsonAndCheckIfLatestKeyExists(Config.bitpopNewUpdateInfoFile)
        if not newDict['latestExists']:
            request.setResponseCode(500)
            return 'Error: Bad new update information file or file does not exist.'

        newInfo = newDict['jsonData']

        outDir = os.path.join(Config.bitpopDirectory, newInfo['latest'])
        if not os.path.exists(outDir):
            request.setResponseCode(500)
            return 'Error: Update directory not created yet.'

        outDir = os.path.join(outDir, request.args['fromVersion'][0])
        if not os.path.exists(outDir):
            os.mkdir(outDir, 0755)
        elif not os.path.isdir(outDir):
            os.remove(outDir)
            os.mkdir(outDir, 0755)
        filename = os.path.join(outDir, Config.installerName)

        try:
            outputStream = open(filename, 'wb')
            outputStream.write(request.args['fileToUpload'][0])
            outputStream.close()

            sha = hashlib.new('sha1')
            sha.update(request.args['fileToUpload'][0])
            hash = base64.b64encode(sha.digest())

            if not newInfo.has_key('delta') or type(newInfo['delta']) != type([]):
                newInfo['delta'] = []
            if not newInfo.has_key('deltaHash') or type(newInfo['deltaHash']) != type([]):
                newInfo['deltaHash'] = []
            newInfo['delta'].append(request.args['fromVersion'][0])
            newInfo['deltaHash'].append(hash)
            bitpopUploadInfoFile = open(Config.bitpopNewUpdateInfoFile, 'w')
            json.dump(newInfo, bitpopUploadInfoFile)
            bitpopUploadInfoFile.close()
        except:
            request.setResponseCode(500) # Internal server error
            return "Error: Internal Server Error. Failed to do some file operation."

        return "OK. File was successfully uploaded to server."