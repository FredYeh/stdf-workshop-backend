const { dateFormat } = require('../utils/format/date')
const path = require('path')
const logger = require('../utils/logger.js')
const ParserService = require('../services/ParserService')
const RecipeBuyoffService = require('../services/RecipeBuyoffService')
const CompareService = require('../services/CompareService')
const RepairServeice = require('../services/RepairService')
const ParseFolderService = require('../services/ParseFolderService')
const HeaderService = require('../services/HeaderService')
const EditorService = require('../services/EditorService')
const textToExcelService = require('../services/textToExcelService')
const ToCsvService = require('../services/ToCsvService')
const DatReaderService = require('../services/DatReaderService')
const RmReadingService = require('../services/RmReadingService')
const MergeSTDFsService = require('../services/MergeSTDFsService')

const UPLOAD_DIR = path.resolve(__dirname, '..', 'files', 'stdf') // 切片儲存目錄

const handleParse = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { reading, fileHash, filename } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename,
    reading: reading
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new ParserService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleRecipe = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash, filename } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new RecipeBuyoffService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleCompare = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash1, filename1, fileHash2, filename2 } = req.body

  const ext1 = path.extname(filename1)
  const ext2 = path.extname(filename2)
  const filePath1 = path.resolve(UPLOAD_DIR, `${fileHash1}${ext1}`)
  const filePath2 = path.resolve(UPLOAD_DIR, `${fileHash2}${ext2}`)
  const fileInfo = {
    filePath1: filePath1,
    filename1: filename1,
    filePath2: filePath2,
    filename2: filename2
  }
  logger.log('info', `File ${filename1} && ${filename2} is start to Parsing`)
  const parser = new CompareService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleRepair = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash, filename } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new RepairServeice(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleFolder = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { folderPath } = req.body

  const fileInfo = {
    folderPath: folderPath
  }
  logger.log('info', `File ${folderPath} is start to Parsing`)
  const parser = new ParseFolderService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleHeader = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash, filename } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new HeaderService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleEditor = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash, filename, editInfo } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename,
    editInfo: editInfo
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new EditorService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleTextToExcel = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash, filename } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new textToExcelService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleToCsv = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash, filename } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new ToCsvService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleReadDat = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash, filename } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new DatReaderService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleRmReading = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash, filename } = req.body

  const ext = path.extname(filename)
  const filePath = path.resolve(UPLOAD_DIR, `${fileHash}${ext}`)
  const fileInfo = {
    filePath: filePath,
    filename: filename
  }
  logger.log('info', `File ${filename} is start to Parsing`)
  const parser = new RmReadingService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

const handleMergeSTDFs = async (req, res) => {
  console.log(req.params, req.body)
  const { socketId } = req.params
  const { fileHash1, filename1, fileHash2, filename2 } = req.body

  const ext1 = path.extname(filename1)
  const ext2 = path.extname(filename2)
  const filePath1 = path.resolve(UPLOAD_DIR, `${fileHash1}${ext1}`)
  const filePath2 = path.resolve(UPLOAD_DIR, `${fileHash2}${ext2}`)
  const fileInfo = {
    filePath1: filePath1,
    filename1: filename1,
    filePath2: filePath2,
    filename2: filename2
  }
  logger.log('info', `File ${filename1} && ${filename2} is start to Parsing`)
  const parser = new MergeSTDFsService(socketId, fileInfo, req.app?.wsClients ?? null)
  const { status, msg } = parser.init()
  if (status === 'success') {
    parser.start()
    res.json({
      code: 20000,
      msg: '已啟動Parser！',
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  } else {
    res.json({
      code: 40100,
      msg: msg,
      data: JSON.stringify({
        date: dateFormat()
      })
    })
  }
}

module.exports = {
  handleParse,
  handleRecipe,
  handleCompare,
  handleRepair,
  handleFolder,
  handleHeader,
  handleEditor,
  handleTextToExcel,
  handleToCsv,
  handleReadDat,
  handleRmReading,
  handleMergeSTDFs
}
