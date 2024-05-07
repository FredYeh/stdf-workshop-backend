const logger = require('../utils/logger.js')
const { PythonShell } = require('python-shell')
const { outputFormat } = require('../utils/format/date')
const path = require('path')
const { signup, getAll, isExists, usedService } = require('../models/service')

module.exports = class RecipeBuyoffService {
  constructor(socketId, fileInfo, wsClients) {
    const { filePath, filename } = fileInfo
    this._socketId = socketId
    this._filePath = filePath
    this._filename = filename
    this._wsClients = wsClients
  }
  init = () => {
    logger.log('info', `ID: ${this._socketId} init RecipeBuyoffService , Target file : ${this._filename}`)
    if (!this._socketId || !this._filename || !this._wsClients) {
      const errorMsg = `${!this._socketId ? 'socketId is empty' : ''},
      ${!this._filename ? 'filename is empty' : ''}
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
    const isServiceExist = await isExists('recipeBuyoff')
    if (!isServiceExist) {
      let isSuccess = await signup('recipeBuyoff')
    }
    const excelName = `${this._filename}_${outputFormat()}.xlsx`
    const parserProcess = new PythonShell('reprobe_site_check.py', {
      mode: 'json',
      pythonOptions: ['-u'], // get print results in real-time
      scriptPath: 'Python',
      args: [this._filePath, excelName]
    })
    parserProcess.on('message', (message) => {
      // const { target, msg } = message
      this._emit(message)
      // console.log(`onMessage ${target},${msg}}`)
    })
    parserProcess.on('stderr', (stderr) => {
      console.log(`onStderr ${stderr}`)
    })
    parserProcess.end((err, code, signal) => {
      if (err) {
        logger.log('verbose', `parserProcess end on error: ${err}`)
        this._emit({
          target: 'recipeBuyoff',
          msg: { err: `${err}`, status: 'error' }
        })
      } else {
        let add1 = usedService('recipeBuyoff')
        this._emit({
          target: 'recipeBuyoff',
          msg: { filename: excelName, status: 'end' }
        })
      }
    })
  }

  _emit = (msgObj) => {
    this._wsClients[this._socketId]?.send(JSON.stringify(msgObj))
  }
}
