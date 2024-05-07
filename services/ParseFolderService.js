const logger = require('../utils/logger.js')
const { PythonShell } = require('python-shell')
const { outputFormat } = require('../utils/format/date')
const path = require('path')
const fs = require('fs')
const { signup, getAll, isExists, usedService } = require('../models/service')

module.exports = class ParseFolderService {
  constructor(socketId, fileInfo, wsClients) {
    const { folderPath } = fileInfo
    this._socketId = socketId
    this._folderPath = folderPath
    this._wsClients = wsClients
  }
  init = () => {
    if (!fs.existsSync(this._folderPath)) {
      return { status: 'error', msg: `Path "${this._folderPath}" not exist!` }
    }
    logger.log('info', `ID: ${this._socketId} init ParseFolderService , Target path : ${this._folderPath}`)
    if (!this._socketId || !this._folderPath || !this._wsClients) {
      const errorMsg = `${!this._socketId ? 'socketId is empty' : ''},
      ${!this._folderPath ? 'filename is empty' : ''}
      ${!this._wsClients ? 'No one is connecting' : ''}
      `
      logger.log('verbose', errorMsg)
      return { status: 'error', msg: errorMsg }
    } else {
      return { status: 'success', msg: '' }
    }
  }
  start = async () => {
    // console.log(this._wsClients[this._socketId])
    const sleep = await new Promise((r) => setTimeout(r, 5000))
    const isServiceExist = await isExists('parseFolder')
    if (!isServiceExist) {
      let isSuccess = await signup('parseFolder')
    }
    const outputFileName = `ParseFolder_${outputFormat()}_repairLog.xlsx`
    const parserProcess = new PythonShell('parseFolder.py', {
      mode: 'json',
      pythonOptions: ['-u'], // get print results in real-time
      scriptPath: 'Python',
      args: [this._folderPath, outputFileName]
    })
    parserProcess.on('message', (message) => {
      //   const { target, msg } = message
      //   console.log(`onMessage ${target},${msg}`)
      this._emit(message)
    })
    parserProcess.on('stderr', (stderr) => {
      console.log(`onStderr ${stderr}`)
    })
    parserProcess.end((err, code, signal) => {
      if (err) {
        logger.log('verbose', `parserProcess end on error: ${err}`)
        this._emit({
          target: 'parseFolder',
          msg: { err: `${err}`, status: 'error' }
        })
      } else {
        let add1 = usedService('parseFolder')
        this._emit({
          target: 'parseFolder',
          msg: { filename: outputFileName, status: 'end' }
        })
      }
    })
  }

  _emit = (msgObj) => {
    this._wsClients[this._socketId]?.send(JSON.stringify(msgObj))
  }
}
