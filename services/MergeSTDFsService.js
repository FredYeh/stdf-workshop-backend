const logger = require('../utils/logger.js')
const { PythonShell } = require('python-shell')
const { outputFormat } = require('../utils/format/date')
const path = require('path')
const { signup, getAll, isExists, usedService } = require('../models/service')

module.exports = class MergeSTDFsService {
  constructor(socketId, fileInfo, wsClients) {
    const { filePath1, filename1, filePath2, filename2 } = fileInfo
    this._socketId = socketId
    this._filePath1 = filePath1
    this._filename1 = filename1
    this._filePath2 = filePath2
    this._filename2 = filename2
    this._wsClients = wsClients
  }
  init = () => {
    logger.log(
      'info',
      `ID: ${this._socketId} init MergeService , Target file : ${this._filename1} & ${this._filename2}`
    )
    if (!this._socketId || !this._filename1 || !this._filename2 || !this._wsClients) {
      const errorMsg = `${!this._socketId ? 'socketId is empty' : ''},
      ${!this._filename1 ? 'filename1 is empty' : ''}
      ${!this._filename2 ? 'filename2 is empty' : ''}
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
    const isServiceExist = await isExists('mergeSTDFs')
    if (!isServiceExist) {
      let isSuccess = await signup('mergeSTDFs')
    }
    const excelName = `${this._filename1}_${outputFormat()}.std`
    const parserProcess = new PythonShell('merge_stdf.py', {
      mode: 'json',
      pythonOptions: ['-u'], // get print results in real-time
      scriptPath: 'Python',
      args: [this._filePath1, this._filePath2, excelName]
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
          target: 'mergeSTDFs',
          msg: { err: `${err}`, status: 'error' }
        })
      } else {
        let add1 = usedService('mergeSTDFs')
        this._emit({
          target: 'mergeSTDFs',
          msg: { filename: excelName, status: 'end' }
        })
      }
    })
  }

  _emit = (msgObj) => {
    this._wsClients[this._socketId]?.send(JSON.stringify(msgObj))
  }
}
